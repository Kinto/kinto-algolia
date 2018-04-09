Changelog
=========

0.1.0 (unreleased)
------------------

**New features**

- Flush indices when server is flushed
- Perform insertions and deletion in bulk for better efficiency
- Add setting to force index refresh on change
- Add heartbeat
- Delete indices when buckets and collections are deleted
- Support quick search from querystring
- Return details about invalid queries in request body
- Support defining mapping from the ``index:schema`` property in the collection metadata

**Bug fixes**

- Only index records if the storage transaction is committed
- Do not allow to search if no read permission on collection or bucket
- Fix empty results response when plugin was enabled after collection creation

**Internal changes**

- Create index when collection is created
