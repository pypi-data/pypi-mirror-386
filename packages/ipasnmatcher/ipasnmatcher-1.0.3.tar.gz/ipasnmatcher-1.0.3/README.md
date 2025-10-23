# ipasnmatcher

A Python package to verify if an IP address belongs to a specific ASN's network ranges using RIPEstat data.

## Features

* Lazy loads prefix data on first match for faster initialization
* Fast IP-to-ASN matching with optimized network range checks
* Built-in caching to minimize API requests
* Optional strict mode to consider only active prefixes
* Uses accurate data from RIPE NCC
* Supports both synchronous and asynchronous usage

## Installation

```bash
pip install ipasnmatcher
```

## Usage

### Synchronous Example

```python
from ipasnmatcher import ASN

# Create an ASN object (prefix data will be lazy-loaded on first match)
asn = ASN("AS151981")

# The first match triggers data loading from RIPEstat API (and caches it)
print(asn.match("153.53.148.45"))  # True or False
```


### Asynchronous Example (Context Managed)

```python
import asyncio
from ipasnmatcher import AsyncASN

async def main():
    # Create an async ASN object (lazy-loads on first async_match)
    async_asn = AsyncASN("AS15169")

    # The first async_match call triggers async data loading
    result = await async_asn.async_match("8.8.8.8")
    print(result)  # True or False

asyncio.run(main())
```

### Asynchronous Example (Manual Lifecycle)

```python
import asyncio
from ipasnmatcher import AsyncASN

asn = AsyncASN("AS15169")

async def main():
    # The first async_match call triggers async data loading
    match = await asn.async_match("8.8.8.8")
    print(match)

    # Manually close the async client to free resources
    await asn.aclose()

asyncio.run(main())
```

## Advanced Usage

```python
asn = ASN(
    asn="AS15169",      # ASN (e.g., Google)
    strict=True,        # Only consider active prefixes
    cache_max_age=7200  # Cache duration in seconds (2 hours)
)
```

### Combining ASN Objects

You can combine multiple ASNs using the `+` operator.
When combined:

* If **any** of the ASNs has `strict=True`, the resulting combined ASN will also be **strict**.
* The combined ASN’s `max_cache_age` will be the **minimum** of the values from the ASNs being merged.

```python
from ipasnmatcher import ASN

google = ASN("AS15169", strict=False, cache_max_age=7200)
cloudflare = ASN("AS13335", strict=True, cache_max_age=3600)

combined = google + cloudflare

# Combined inherits strict=True and cache_max_age=3600
print(combined.match("8.8.8.8"))   # True (Google)
print(combined.match("1.1.1.1"))   # True (Cloudflare)
```

`repr()` shows the full combination:

```
ASN(asn='AS15169', strict=True, cache_max_age=3600) + ASN(asn='AS13335', strict=True, cache_max_age=3600)
```

## Parameters

```python
ASN(asn: str, strict: bool = False, cache_max_age: int = 3600)
```

* `asn`: ASN identifier in format `"AS12345"`
* `strict`: If `True`, only prefixes currently active are considered (default: `False`)
* `cache_max_age`: Cache lifetime in seconds (default: `3600`)

## How it works

* Data is **lazy-loaded** — the first `match()` or `async_match()` triggers prefix loading from the RIPEstat API.
* Prefix data is cached locally in `.ipasnmatcher_cache/{asn}.json`.
* Subsequent matches use cached data if it’s fresh (not older than `cache_max_age`).
* Matching is done efficiently using Python’s `ipaddress` module.


## Async Performance Test

```python
import asyncio
from ipasnmatcher import AsyncASN
from time import perf_counter, sleep

t1 = perf_counter()
asn1 = AsyncASN("AS136618", cache_max_age=1)
asn2 = AsyncASN("AS151981") # has default cache_max_age of 3600
t2 = perf_counter()

print("took:",t2-t1,"to initialize")

t2 = perf_counter()
asn = asn1 + asn2 # when combined together, prefixes are fetched synchronously(blocking, non-concurrent) and loaded into cache
# Prefixes are fetched from api and loaded in cache when you either combine ASN objects or run the first .match() / async_match() method
# the combined ASN object will have the lower cache_max_age, 
# here asn1 has 1 second cache_max_age, and asn2 has 3600 seconds
# so 1 second will be the cache_max_age of the combined asn object
t3 = perf_counter()

print("combining took:",t3-t2,"seconds")

async def main():
    ip = "103.67.66.0"
    print("cache_max_age of combined asn object is:", asn._cache_max_age)


    t3 = perf_counter()
    match = await asn.async_match(ip)
    # matches using previously loaded cache
    t4 = perf_counter()


    print(match)

    print("matching using loaded cache took:",t4-t3,"seconds")

    sleep(1.5) # waiting 1.5 seconds to let the cache expire

    t4 = perf_counter()
    match = await asn.async_match(ip) # cache is loaded asynchronously if it's expired, using the same TCP connection 
    # If cache is fetched by any async method (e.g via __aenter__() or .async_match() ) 
    # Then established TCP connection is kept safe for further use
    t5 = perf_counter()

    print(match)

    print("matching + reloading expired cache using newly established TCP connection:",t5-t4,"seconds") 

    sleep(1.5) # again waiting 1.5 seconds to let the cache expire

    for _ in range(3):
        # Running it three times to benchmark how much faster re-using TCP connection can be
        tx = perf_counter()
        match = await asn.async_match(ip) # cache is loaded asynchronously if it's expired, using the same TCP connection 
        # If cache is fetched by any async method (e.g via __aenter__() or .async_match() ) 
        # then established TCP connection is kept safe for further use
        ty = perf_counter()
        print(match)

        print("matching + reloading expired cache using previously established TCP connection:",ty-tx,"seconds") 
        await asyncio.sleep(1.5)


    await asn.aclose() # Closes the TCP connection & releases async resources
    sleep(1.5) # again, waiting 1.5 seconds to let the cache expire


    t6 = perf_counter()
    match = await asn.async_match(ip) # Prefixes are fetched from api with a new TCP connection since last connection was closed/ dead
    t7 = perf_counter()


    print(match)

    print("matching + reloading expired cache using new TCP connection:",t7-t6,"seconds")
    await asn.aclose() # Closes the TCP connection

asyncio.run(main())
```

```bash
```
took: 0.0005818130000534438 to initialize
combining took: 1.2682075939999322 seconds
cache_max_age of combined asn object is: 1
True
matching using loaded cache took: 4.192099993360898e-05 seconds
True
matching + reloading expired cache using newly established TCP connection: 0.6581063339999673 seconds
True
matching + reloading expired cache using previously established TCP connection: 0.15290267000000313 seconds
True
matching + reloading expired cache using previously established TCP connection: 0.15268935999995392 seconds
True
matching + reloading expired cache using previously established TCP connection: 0.15698356899997634 seconds
True
matching + reloading expired cache using new TCP connection: 0.6321861889999809 seconds
```


## Use Cases

* Network security and traffic validation
* CDN traffic routing based on ASN ownership
* IP classification by network operators
* Compliance monitoring of network connections

## GitHub

Star or fork this project on [GitHub](https://github.com/Itsmmdoha/ipasnmatcher).

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/Itsmmdoha/ipasnmatcher/blob/main/LICENSE) file for details.
