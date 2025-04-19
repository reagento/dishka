.. include:: <isonum.txt>

For most cases we operate single events like HTTP-requests. In this case we operate only 2 scopes: ``APP`` and ``REQUEST``.
Websockets are different: for one application you have multiple connections (one per client) and each connection delivers multiple messages.
To support this we use additional scope: ``SESSION``:

    ``APP`` |rarr| ``SESSION`` |rarr| ``REQUEST``