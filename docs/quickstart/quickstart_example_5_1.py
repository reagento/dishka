# APIClient is bound to Scope.APP, so it is accessible here
client_1 = container.get(APIClient)
client_2 = container.get(APIClient)  # the same APIClient instance
assert client_1 is client_2
