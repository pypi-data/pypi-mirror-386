use crate::pip::parse_requirement;
use crate::uv::uv_cache;
use rkyv::{Archive, Archived, Deserialize, deserialize};
use uv_normalize::PackageName;
use uv_pep440::{Version, VersionSpecifier};
use uv_pep508::Requirement;
use uv_pypi_types::Yanked;

use rkyv::api::high::HighDeserializer;
use std::collections::HashSet;
use tokio::sync::Semaphore;
use uv_client::{
    BaseClientBuilder, MetadataFormat, OwnedArchive, RegistryClient, RegistryClientBuilder,
    SimpleMetadata, SimpleMetadatum, VersionFiles,
};
use uv_distribution_types::IndexCapabilities;

/// Shadow `RegistryClient` to hide new complexity of .simple
struct SimplePypi(RegistryClient);

impl SimplePypi {
    /// Use `RegistryClient.package_metadata` to lookup a package on default package index
    async fn lookup(
        &self,
        package_name: &PackageName,
    ) -> anyhow::Result<Vec<OwnedArchive<SimpleMetadata>>> {
        // 1 permit is sufficient
        let download_concurrency = Semaphore::new(1);

        let response = self
            .0
            .package_metadata(
                package_name,
                None,
                &IndexCapabilities::default(),
                &download_concurrency,
            )
            .await?;

        let mapped: Vec<_> = response
            .into_iter()
            .filter_map(|(_url, metadata)| match metadata {
                MetadataFormat::Simple(data) => Some(data),
                MetadataFormat::Flat(_) => None,
            })
            .collect();

        Ok(mapped)
    }
}

impl Default for SimplePypi {
    /// Create a (default) Registry
    fn default() -> Self {
        let cache = uv_cache();
        let base_client = BaseClientBuilder::default();
        let inner = RegistryClientBuilder::new(base_client, cache).build();

        Self(inner)
    }
}

/// usage: e.g. `let x: Option<VersionFiles> = deserialize(&metadatum.files);`
/// Note: pycharm will probably complain, but it WILL work for `ArchivedSimpleMetadatum`!
pub fn rkyv_deserialize<T: Archive>(archived: &Archived<T>) -> Option<T>
where
    T::Archived: Deserialize<T, HighDeserializer<rkyv::rancor::Error>>,
{
    deserialize(archived).ok()
}

fn deserialize_metadata(datum: &Archived<SimpleMetadatum>) -> Option<SimpleMetadatum> {
    // for some reason, pycharm doesn't understand this type (but it compiles)
    let full: Option<SimpleMetadatum> = rkyv_deserialize(datum);
    full
}

fn is_yanked(yanked: Option<Box<Yanked>>) -> bool {
    let Some(boxed) = yanked else {
        // early return if yanked is None
        return false;
    };

    // dereference to get value out of box:
    match *boxed {
        Yanked::Reason(_) => true,
        Yanked::Bool(status) => status,
    }
}

fn find_non_yanked_versions(metadata: &OwnedArchive<SimpleMetadata>) -> HashSet<Version> {
    let files_data: Vec<VersionFiles> = metadata
        .iter()
        .filter_map(|metadatum| rkyv_deserialize(&metadatum.files))
        .collect();

    let mut valid_versions = HashSet::new();

    for file in files_data {
        for source_dist in file.source_dists {
            if !is_yanked(source_dist.file.yanked) {
                valid_versions.insert(source_dist.name.version);
            }
        }
        for wheel in file.wheels {
            if !is_yanked(wheel.file.yanked) {
                valid_versions.insert(wheel.name.version);
            }
        }
    }

    valid_versions
}

pub async fn get_versions_for_packagename(
    package_name: &PackageName,
    stable: bool,
    constraint: Option<VersionSpecifier>,
) -> Vec<Version> {
    let mut versions: Vec<Version> = vec![];

    let client = SimplePypi::default();

    let data = match client.lookup(package_name).await {
        Err(err) => {
            eprintln!("Something went wrong: {err};");
            return versions;
        },
        Ok(data) => data,
    };

    if let Some(metadata) = data.iter().next_back() {
        let not_yanked = find_non_yanked_versions(metadata);

        versions = metadata
            .iter()
            .filter_map(|metadatum| {
                rkyv_deserialize(&metadatum.version).filter(|version| not_yanked.contains(version))
            })
            .collect();
    }

    if stable {
        versions.retain(|version| !version.any_prerelease());
    }

    if let Some(specifier) = constraint {
        versions.retain(|version| specifier.contains(version));
    }

    versions
}

pub async fn get_latest_version_for_packagename(
    package_name: &PackageName,
    stable: bool,
    constraint: Option<VersionSpecifier>,
) -> Option<Version> {
    let versions = get_versions_for_packagename(package_name, stable, constraint).await;

    versions.last().cloned()
}
#[expect(
    dead_code,
    reason = "More generic than the used code above (which only looks at version info)"
)]
pub async fn get_pypi_data_for_packagename(package_name: &PackageName) -> Option<SimpleMetadatum> {
    let client = SimplePypi::default();

    let data = client.lookup(package_name).await.ok()?;

    if let Some(metadata) = data.iter().next_back()
        && let Some(latest) = metadata.iter().next_back()
    {
        return deserialize_metadata(latest);
    }

    None
}

pub async fn get_latest_version_for_requirement(
    req: &Requirement,
    stable: bool,
    constraint: Option<VersionSpecifier>,
) -> Option<Version> {
    get_latest_version_for_packagename(&req.name, stable, constraint).await
}

pub async fn get_latest_version(
    package_spec: &str,
    stable: bool,
    constraint: Option<VersionSpecifier>,
) -> Option<Version> {
    let (requirement, _) = parse_requirement(package_spec).await.ok()?;
    get_latest_version_for_requirement(&requirement, stable, constraint).await
}
