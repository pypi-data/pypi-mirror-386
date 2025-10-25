# AWS::Location Construct Library

<!--BEGIN STABILITY BANNER-->---


![cdk-constructs: Experimental](https://img.shields.io/badge/cdk--constructs-experimental-important.svg?style=for-the-badge)

> The APIs of higher level constructs in this module are experimental and under active development.
> They are subject to non-backward compatible changes or removal in any future version. These are
> not subject to the [Semantic Versioning](https://semver.org/) model and breaking changes will be
> announced in the release notes. This means that while you may use them, you may need to update
> your source code when upgrading to a newer version of this package.

---
<!--END STABILITY BANNER-->

This module is part of the [AWS Cloud Development Kit](https://github.com/aws/aws-cdk) project.

Amazon Location Service lets you add location data and functionality to applications, which
includes capabilities such as maps, points of interest, geocoding, routing, geofences, and
tracking. Amazon Location provides location-based services (LBS) using high-quality data from
global, trusted providers Esri and HERE. With affordable data, tracking and geofencing
capabilities, and built-in metrics for health monitoring, you can build sophisticated
location-enabled applications.

## Geofence Collection

Geofence collection resources allow you to store and manage geofences—virtual boundaries on a map.
You can evaluate locations against a geofence collection resource and get notifications when the location
update crosses the boundary of any of the geofences in the geofence collection.

```python
# key: kms.Key


location.GeofenceCollection(self, "GeofenceCollection",
    geofence_collection_name="MyGeofenceCollection",  # optional, defaults to a generated name
    kms_key=key
)
```

Use the `grant()` or `grantRead()` method to grant the given identity permissions to perform actions
on the geofence collection:

```python
# role: iam.Role


geofence_collection = location.GeofenceCollection(self, "GeofenceCollection",
    geofence_collection_name="MyGeofenceCollection"
)

geofence_collection.grant_read(role)
```

## Tracker

A tracker stores position updates for a collection of devices. The tracker can be used to query the devices' current location or location history. It stores the updates, but reduces storage space and visual noise by filtering the locations before storing them.

For more information, see [Trackers](https://docs.aws.amazon.com/location/latest/developerguide/geofence-tracker-concepts.html#tracking-overview).

To create a tracker, define a `Tracker`:

```python
# key: kms.Key


location.Tracker(self, "Tracker",
    tracker_name="MyTracker",  # optional, defaults to a generated name
    kms_key=key
)
```

Use the `grant()`, `grantUpdateDevicePositions()` or `grantRead()` method to grant the given identity permissions to perform actions
on the geofence collection:

```python
# role: iam.Role


tracker = location.Tracker(self, "Tracker",
    tracker_name="MyTracker"
)

tracker.grant_read(role)
```

If you want to associate a tracker with geofence collections, define a `geofenceCollections` property or use the `addGeofenceCollections()` method.

```python
# geofence_collection: location.GeofenceCollection
# geofence_collection_for_add: location.GeofenceCollection
# tracker: location.Tracker


tracker = location.Tracker(self, "Tracker",
    tracker_name="MyTracker",
    geofence_collections=[geofence_collection]
)

tracker.add_geofence_collections(geofence_collection_for_add)
```

## API key

API keys are a key value that is associated with specific Amazon Location Service resources or API in your AWS account, and specific actions that you can perform on those resources.
You can use an API key in your application to make unauthenticated calls to the Amazon Location APIs for those resources.

For more information, see [Use API keys to authenticate](https://docs.aws.amazon.com/location/latest/developerguide/using-apikeys.html).

To create an API key, define an `ApiKey`:

```python
location.ApiKey(self, "APIKeyAny",
    # specify allowed actions
    allow_maps_actions=[location.AllowMapsAction.GET_STATIC_MAP
    ],
    allow_places_actions=[location.AllowPlacesAction.GET_PLACE
    ],
    allow_routes_actions=[location.AllowRoutesAction.CALCULATE_ISOLINES
    ]
)
```

> Note: `ApiKey` construct only supports [Enhanced Places, Routes, and Maps](https://aws.amazon.com/blogs/aws/announcing-new-apis-for-amazon-location-service-routes-places-and-maps/) This API key grants access to AWS-managed Places, Routes, and Maps.

## Legacy Resources

AWS has released new [Enhanced Places, Routes, and Maps](https://aws.amazon.com/about-aws/whats-new/2024/11/amazon-location-service-enhanced-places-routes-maps/?nc1=h_ls). Since these use AWS-managed resources, users no longer need to create Maps, Places, and Routes resources themselves.

As a result, the following constructs are now considered legacy.

For more information, see [developer guide](https://docs.aws.amazon.com/location/latest/developerguide/what-is.html).

### Map

The Amazon Location Service Map resource gives you access to the underlying basemap data for a map.
You use the Map resource with a map rendering library to add an interactive map to your application.
You can add other functionality to your map, such as markers (or pins), routes, and polygon areas, as needed for your application.

For information about how to use map resources in practice, see [Using Amazon Location Maps in your application](https://docs.aws.amazon.com/location/latest/developerguide/using-maps.html).

To create a map, define a `Map`:

```python
location.Map(self, "Map",
    map_name="my-map",
    style=location.Style.VECTOR_ESRI_NAVIGATION,
    custom_layers=[location.CustomLayer.POI]
)
```

Use the `grant()` or `grantRendering()` method to grant the given identity permissions to perform actions
on the map:

```python
# role: iam.Role


map = location.Map(self, "Map",
    style=location.Style.VECTOR_ESRI_NAVIGATION
)
map.grant_rendering(role)
```

### Place Index

A key function of Amazon Location Service is the ability to search the geolocation information.
Amazon Location provides this functionality via the Place index resource. The place index includes
which [data provider](https://docs.aws.amazon.com/location/latest/developerguide/what-is-data-provider.html)
to use for the search.

To create a place index, define a `PlaceIndex`:

```python
location.PlaceIndex(self, "PlaceIndex",
    place_index_name="MyPlaceIndex",  # optional, defaults to a generated name
    data_source=location.DataSource.HERE
)
```

Use the `grant()` or `grantSearch()` method to grant the given identity permissions to perform actions
on the place index:

```python
# role: iam.Role


place_index = location.PlaceIndex(self, "PlaceIndex")
place_index.grant_search(role)
```

### Route Calculator

Route calculator resources allow you to find routes and estimate travel time based on up-to-date road network and live traffic information from your chosen data provider.

For more information, see [Routes](https://docs.aws.amazon.com/location/latest/developerguide/route-concepts.html).

To create a route calculator, define a `RouteCalculator`:

```python
location.RouteCalculator(self, "RouteCalculator",
    route_calculator_name="MyRouteCalculator",  # optional, defaults to a generated name
    data_source=location.DataSource.ESRI
)
```

Use the `grant()` or `grantRead()` method to grant the given identity permissions to perform actions
on the route calculator:

```python
# role: iam.Role


route_calculator = location.RouteCalculator(self, "RouteCalculator",
    data_source=location.DataSource.ESRI
)
route_calculator.grant_read(role)
```
