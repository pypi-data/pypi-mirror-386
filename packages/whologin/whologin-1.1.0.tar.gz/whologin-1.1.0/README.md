## WhoLogin Python SDK

Python SDK for interacting with the WhoLogin API.

### Installation

```bash
pip install whologin
```

### Quick Example

```python
from whologin import WhoLoginAPI, ProfileBuilder

api = WhoLoginAPI('YOUR-API-URL', 'YOUR-API-KEY')

# Create and update quickly (set only what you need)
created = api.profile.create(
    ProfileBuilder()
        .with_profile_name('Minimal')
        .with_tag('GettingStarted')
)

# Update using builder: note + tags + proxy
api.profile.update(
    created['id'],
    ProfileBuilder()
        .with_note('Updated')
        .with_tags(['Updated', 'Example'])
        .with_direct_proxy()
)
```

### Quick Example (async)

```python
import asyncio
from whologin import AsyncWhoLoginAPI, ProfileBuilder

async def main():
    async with AsyncWhoLoginAPI('YOUR-API-URL', 'YOUR-API-KEY') as api:
        created = await api.profile.create(
            ProfileBuilder()
                .with_profile_name('Minimal')
                .with_tag('GettingStarted')
        )
        await api.profile.update(
            created['id'],
            ProfileBuilder()
                .with_note('Updated')
                .with_tags(['Updated', 'Example'])
                .with_direct_proxy()
        )

asyncio.run(main())
```

### Examples

See more complete examples in the `examples/` folder:

- `examples/basic_sync.py`
- `examples/basic_async.py`
- `examples/extension_manager_sync.py`
- `examples/extension_manager_async.py`
- `examples/open_with_playwright_sync.py`
- `examples/open_with_playwright_async.py`

### Error handling

All API calls raise `WhoLoginAPIError` when the backend returns `{ success: false }`.
Wrap calls in `try/except` and read the exception message for a user-friendly reason.

```python
from whologin import WhoLoginAPI, WhoLoginAPIError, ProfileBuilder

api = WhoLoginAPI('YOUR-API-URL', 'YOUR-API-KEY')

try:
    api.profile.update('non-existent-id', ProfileBuilder().with_note('x'))
except WhoLoginAPIError as e:
    print('API failed:', e)
```

### API Overview

#### Profile Endpoints

- `create(requestOrBuilder)`
- `getAll()`
- `search(searchRequest)`
- `getById(profileId)`
- `getListOpen()`
- `update(profileId, requestOrBuilder)`
- `delete(profileId)`
- `open(profileId, openRequest?)`
- `close(profileId)`
- `addTags(profileId, tags)`
- `removeTags(profileId, tags)`
- `exportCookies(profileId)`
- `importCookies(profileId, cookies)`
- `geolocate(profileId)`
- `getTrash()`
- `deleteFromTrash(profileId)`
- `cleanTrash()`
- `restoreAllFromTrash()`
- `restoreFromTrash(profileId)`

#### Proxy Endpoints

- `getAll()`
- `create(createRequest)`
- `update(proxyId, updateRequest)`
- `delete(proxyId)`
- `geolocateById(proxyId)`
- `geolocate(geolocateRequest)`

#### Tag Endpoints

- `getAll()`
- `create(createRequest)`
- `update(tagId, updateRequest)`
- `delete(tagId)`
