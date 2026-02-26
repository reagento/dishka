# The sub-container to access shorter-living objects
with container() as request_container:
    # Service, DBGateway, and Connection are bound to Scope.REQUEST,
    # so they are accessible here
    service_1 = request_container.get(Service)
    service_2 = request_container.get(Service)  # the same service instance
    assert service_1 is service_2

# Since we exited the context manager, the sqlite3 connection is now closed

# The new subcontainer has a new lifespan for event processing
with container() as request_container:
    service = request_container.get(Service)  # the new service instance
