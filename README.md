## DIshka - DI by Tishka17

Minimal DI framework with scopes

### Quickstart

1. Create Scopes enum
2. Create Provider subclass. 
3. Mark methods which actually create depedencies with `@provide` decorator
4. Do not forget typehints
5. Create Container instance passing providers
6. Call `get` to get dependency and use context manager to get deeper through scopes
7. Add decorators and middleware for your framework

See [examples](examples/sync_simple.py)