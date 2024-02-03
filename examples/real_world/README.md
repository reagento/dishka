## Real world app example

In this example we try to simulate real world application rich of classes.

**Note**: it is not a guide on good architecture design, it is just an example how to use `dishka`

The folder structure is simplified as we do not have real code here, but just some fake implementations.
Anyway, the application can be split into several parts:

1. **Use case interactors**. Here is main business logic of application. But as it cannot work without some database and additional services we define Protocols here as well.
2. **Database gateway**. It implements some logic related to database calls. 
   As we have multiple gateways here they need to share the same database connection otherwise we cannot control transactions here. 
   For simplicity, we do not have separate implementation of unit of work, but reuse database connection directly. This can be also suitable if we use ORM. 
3. **API client**. It could be any external API client/adapter.  
4. **Presentation** contains some handler or web-views. Here we bind our logic to framework.
5. **IoC-container** contains the configuration of all mentions classes bound together (dishka Providers are placed here)
6. **Main**. Some startup and configuration logic. We combine all parts together
7. **Tests**. We reuse some parts and replace others with mocks. Here we do some calls and checks 


Talking about _lifetime_ of objects we can say that:
1. _API Client_ most probably can be created once and then reuses multiple times. 
2. _Database gateways, database connection, unit of work_, and corresponding _interactors_ are valid only during lifetime of request. 
   Multiple concurrent requests should have their data processed correctly, so they will have different instances of these classes

```
   ┌────────────────┐
   │Warehouse client├────────────────────►─────┐
   └────────────────┘                          │
                       ┌────────────┐          │
                 ┌─────►Unit of work├────►─────┤
                 │     └────────────┘          │
                 │                            ┌▼─────────┐
   ┌─────────────┴──┐  ┌─────────────┐        │Interactor│
   │DB Connection   ├──►Users gateway├───────►└▲─────────┘
   └─────────────┬──┘  └─────────────┘         │
                 │                             │
                 │     ┌─────────────────┐     │
                 └─────►Products gateway ├─►───┘
                       └─────────────────┘
```