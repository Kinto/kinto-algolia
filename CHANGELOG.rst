Changelog
=========

1.2.0 (unreleased)
------------------

- Nothing changed yet.


1.1.0 (2019-04-26)
------------------

- Upgrade to algoliasearch 2.0


1.0.0 (2019-02-08)
------------------

- Add support for collections whitelist. (#6)


0.2.0 (2018-07-18)
------------------

**Bug fixes**

- Update algolia settings.


0.1.1 (2018-06-06)
------------------

**Bug fixes**

- Fix reindex command.


0.1.0 (2018-04-12)
------------------

**New features**

- Flush indices when server is flushed
- Perform insertions and deletion in bulk for better efficiency
- Add heartbeat
- Delete indices when buckets and collections are deleted
- Support quick search from querystring
- Support defining mapping from the ``algolia:settings`` property in the collection metadata

**Bug fixes**

- Only index records if the storage transaction is committed
- Do not allow to search if no read permission on collection or bucket
- Fix empty results response when plugin was enabled after collection creation

**Internal changes**

- Create index when collection is created
