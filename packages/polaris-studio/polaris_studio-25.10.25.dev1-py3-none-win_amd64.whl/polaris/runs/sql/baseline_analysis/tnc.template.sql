-- Copyright (c) 2025, UChicago Argonne, LLC
-- BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
DROP TABLE IF EXISTS tnc_request_stats;
CREATE TABLE tnc_request_stats as
    SELECT
        tnc_operator,
        service_mode,
        case
            when assigned_vehicle IS NULL then 'UNASSIGNED'
            else 'ASSIGNED'
        end as assigned_status,        
        avg(case when assigned_vehicle IS NOT NULL then (assignment_time-request_time)/60.0 else 0 end) as time_to_assign,
        avg(case when assigned_vehicle IS NOT NULL then (pickup_time-request_time-prep_duration)/60.0 else 0 end) as wait,
        avg(case when assigned_vehicle IS NOT NULL then (dropoff_time-pickup_time)/60.0 else 0 end) as ivtt,
        avg(case when assigned_vehicle IS NOT NULL then prep_duration/60.0 else 0 end) as prep_duration,
        scaling_factor*sum(case when assigned_vehicle IS NOT NULL then distance else 0 end) as pmt,
        scaling_factor*sum(case when assigned_vehicle IS NOT NULL then (dropoff_time-request_time)/3600 else 0 end) as pht,
        scaling_factor*count(*) as demand
    FROM     "TNC_Request"
    GROUP BY 1,2,3;

DROP TABLE IF EXISTS tnc_trip_stats;
CREATE TABLE tnc_trip_stats AS
    SELECT
        tnc_operator,
        mode,
        case
            when final_status = -1 then 'PICKUP'
            when final_status = -2 then 'DROPOFF'
            when final_status = -4 then 'CHARGING'
        end as status,
        case
            when passengers = 0 then 'UNOCCUPIED'
            else 'OCCUPIED'
        end as occupied_status,
        scaling_factor*sum(travel_distance)/1609.34 as vmt,
        scaling_factor*sum(end-start)/3600 as vht
    FROM     TNC_Trip
    GROUP BY 1,2,3,4;

DROP TABLE IF EXISTS avo_by_tnc_operator;
CREATE TABLE avo_by_tnc_operator AS
    SELECT   tnc_operator, 'AVO_trips' AS metric, avg(passengers) AS AVO
    FROM     TNC_Trip
    GROUP BY 1
UNION
    SELECT   tnc_operator, 'AVO_dist' AS metric, sum(passengers*1.0*travel_distance)/sum(travel_distance) AS AVO
    FROM     TNC_Trip
    GROUP BY 1
UNION
    SELECT   tnc_operator, 'AVO_trips_revenue' AS metric, avg(passengers) AS AVO
    FROM     TNC_Trip
    WHERE    passengers > 0
    GROUP BY 1
UNION
    SELECT   tnc_operator, 'AVO_dist_revenue' AS metric, sum(passengers*1.0*travel_distance)/sum(travel_distance) AS AVO
    FROM     TNC_Trip
    WHERE    passengers > 0 and travel_distance > 0
    GROUP BY 1;