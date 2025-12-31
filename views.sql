-- View1 : ALL_IB
create or replace view CPS_DB.CPS_DSCI_BR.ALL_IB(
	INSTANCE_ID,
	COVERED_STATUS,
	COVERAGE_STATUS,
	INSTALLED_AT_COUNTRY,
	SERVICE_LIST_PRICE,
	PRODUCT_LIST_PRICE,
	GLOBAL_PRODUCT_LIST_PRICE,
	SERVICE_LIST_PRICE_X_QUANTITY,
	PRODUCT_LIST_PRICE_X_QUANTITY,
	PRODUCT_LIST_PRICE_GPL_US_X_QUANTITY,
	QUANTITY,
	PRODUCT_FAMILY,
	DEVICE_LEVEL_REAL_PRODUCT_TYPE,
	IB_PRODUCT_TYPE_RAW,
	LAST_DATE_OF_SUPPORT,
	LAST_DATE_OF_RENEWAL,
	LAST_DATE_OF_SERVICE_ATTACH,
	MSS_STATUS,
	LINEAGE_SERIAL_NUMBER,
	MAPPED_TO_SERVICE_FLAG,
	ITEM_STATUS_C3,
	ITEM_STATUS_MFG,
	PRODUCT_TYPE_RAW,
	CATALOG_PRODUCT_TYPE,
	PID_CATEGORY,
	ITEM_NAME,
	MONETIZATION_TYPE,
	INSTANCE_STATUS_DESC,
	CONFIG_TYPE,
	ZERO_DOLLAR_SVC_FLAG,
	IS_PARENT,
	DEVICE_LEVEL_IS_LDOS_FLAG,
	SERIALIZED_FLAG,
	END_OF_CHANGE_DT,
	END_OF_MANUFACTURING_DT,
	END_OF_NEW_SVC_ATTACHMENT_DT,
	END_OF_SOFTWARE_MAINTENANCE_DT,
	END_OF_ROUTINE_FAIL_ANLYSYS_DT,
	EOL_SOFTWARE_AVAILABLE_DT,
	END_OF_SFTWR_LICENSE_AVAIL_DT,
	EOL_SIGNATURE_RELEASE_DT,
	END_OF_SVC_CONTRACT_RNWL_DT,
	END_OF_TAC_ENGG_SUPPORT_DT,
	END_OF_SALE_DT,
	GU_ID,
	GU_NAME,
	DECOM_ISH,
	LAST_ADD_TO_COVERAGE_DATE,
	SHIP_DATE,
	IS_FRU,
	GREATEST_SERVICE_LIST_PRICE,
	GREATEST_PRODUCT_LIST_PRICE,
	ORPHAN_MINOR_1,
	ORPHAN_MINOR_2
) as
    select * from  CPS_DSCI_ARCHIVE.all_ib_new;


-- view 2: CAM_ACTIVITY_SIGNOFF

create or replace view CPS_DB.CPS_DSCI_BR.CAM_ACTIVITY_SIGNOFF(
	SOLD_AS_SERVICE_NAME,
	BOOKING_COUNTRY,
	BUYING_PROGRAM_NAME,
	PRICING_MODEL_NAME,
	BOOKED_THEATER,
	REFERENCE_BOOKING_CONTRACT,
	NOTES,
	SIGN_OFF_IDENTITY,
	SIGNOFF_METHOD,
	DEFER_SIGNOFF_REASON,
	ENGAGEMENT_NAME,
	DC_ENGAGEMENT_ID,
	BOOKING_CONTRACT,
	USER_TITLE,
	FISCAL_QTR_SORTED_NAME,
	FISCAL_MTH_SORTED_NAME,
	CAL_WEEK_SORTED_SHORT_NAME,
	CREATE_DTM,
	SIGNOFF_DAYS_AGO,
	DC_USER_ID,
	SIGNOFF_CREATE_DTM,
	IS_LAST_SIGNOFF,
	LEVEL6_CISCO_WORKER_NAME,
	LEVEL7_CISCO_WORKER_NAME,
	LEVEL8_CISCO_WORKER_NAME,
	LEVEL9_CISCO_WORKER_NAME,
	EMP_CCO_ID_MASKED,
	MGR_NAME,
	THEATER,
	ACCOUNT_NAME,
	SOLD_AS_SW_ALLOCATION,
	SOLD_AS_HW_ALLOCATION
) as

with mx_so_per_bc as ( -- max non deferred signoff regardless of type where agreemnt > 3 month old
                     select s.BOOKING_CONTRACT, s.CREATE_DTM as last_signoff_date,s.DC_USER_ID
                            ,rank() over ( partition by s.BOOKING_CONTRACT  order by s.CREATE_DTM desc, s.DC_USER_ID ) as orderv
                      from CPS_DSCI_API.DC_WF_IB_SIGNOFF s
                               join CPS_DSCI_API.dc_BOOKINGS_CONTRACTS c
                                    on (c.BOOKING_CONTRACT = s.BOOKING_CONTRACT and c.is_deleted = 'F')
                      where current_date between c.AGREEMENT_START_DATE and dateadd(day, 30, c.AGREEMENT_END_DATE)
                      and s.SIGNOFF_METHOD_ID != 7 -- DEFERED
                      and s.is_deleted ='F'
                      group by s.BOOKING_CONTRACT,s.CREATE_DTM, s.DC_USER_ID
),so as (
            select s.notes, i.SIGN_OFF_IDENTITY, m.SIGNOFF_METHOD, sor.DEFER_SIGNOFF_REASON,  e.ENGAGEMENT_NAME, e.DC_ENGAGEMENT_ID ,
                   s.BOOKING_CONTRACT, u.USER_TITLE,
                   d.FISCAL_QTR_SORTED_NAME, d.FISCAL_MTH_SORTED_NAME , d.CAL_WEEK_SORTED_SHORT_NAME,
                   s.CREATE_DTM, datediff(day,s.CREATE_DTM, current_timestamp) as signoff_days_ago, s.DC_USER_ID,
                   s.CREATE_DTM as SIGNOFF_CREATE_DTM,
                   case when mm.BOOKING_CONTRACT is null then 'N' else 'Y' end as is_last_signoff
            from    CPS_DSCI_API.DC_WF_IB_SIGNOFF s
            join CPS_DSCI_API.dc_typ_defer_signoff_reason sor on ( sor.DEFER_SIGNOFF_REASON_ID=s.DEFER_SIGNOFF_REASON_ID)
            join CPS_DSCI_API.DC_ENGAGEMENT_HDR e on (e.dc_engagement_id =s.dc_engagement_id)
            JOIN CPS_DSCI_API.DC_TYP_SIGNOFF_METHOD m on (m.SIGNOFF_METHOD_ID=s.SIGNOFF_METHOD_ID )
            JOIN CPS_DSCI_API.DC_TYP_SIGN_OFF_IDENTITY i on (i.SIGN_OFF_IDENTITY_ID =s.SIGN_OFF_IDENTITY_ID )
            join CPS_DSCI_API.DC_USERS u on (s.DC_USER_ID = u.USER_ID )
            join CPS_DSCI_ARCHIVE.DIM_DATE_NEW d on (d.DATE = s.CREATE_DTM::date)
            left join mx_so_per_bc mm on (
                mm.BOOKING_CONTRACT=s.BOOKING_CONTRACT
                    and mm.last_signoff_date=s.CREATE_DTM
                    and mm.orderv = 1
                    and mm.DC_USER_ID=s.DC_USER_ID)
            where s.is_deleted = 'F'

    ), hier as (
            select distinct  LEVEL6_CISCO_WORKER_NAME, LEVEL7_CISCO_WORKER_NAME, LEVEL8_CISCO_WORKER_NAME,LEVEL9_CISCO_WORKER_NAME,
                u.USER_ID, h.EMP_NAME,  h.mgr_name,
                   h.emp_cco_id_masked,
                   h.dc_theater as THEATER,
                   u.USER_TITLE as ROLE,
                    u.USER_ID as DC_USER_ID
            from CPS_DSCI_API.DC_USERS u
                     left join CPS_DSCI_API.organizational_hierarchy h on (concat(h.emp_cco_id, '@cisco.com') = u.CISCO_CCO_ID)
            where u.IS_DELETED = 'F'
              and emp_cco_id_masked is not null
    )
select st.SOLD_AS_SERVICE_NAME,
       c.booking_country ,
        bp.BUYING_PROGRAM_NAME,
        pm.PRICING_MODEL_NAME,
        t.THEATER_NAME as booked_theater,
        c.BOOKING_CONTRACT as reference_booking_contract,
       so.*,
       nvl(hier.LEVEL6_CISCO_WORKER_NAME, 'Not Assigned') as LEVEL6_CISCO_WORKER_NAME,
       nvl(hier.LEVEL7_CISCO_WORKER_NAME, 'Not Assigned') as LEVEL7_CISCO_WORKER_NAME,
       nvl(hier.LEVEL8_CISCO_WORKER_NAME, 'Not Assigned') as LEVEL8_CISCO_WORKER_NAME,
       nvl(hier.LEVEL9_CISCO_WORKER_NAME, 'Not Assigned') as LEVEL9_CISCO_WORKER_NAME,
       nvl(hier.emp_cco_id_masked, 'Not Assigned') as emp_cco_id_masked,
       nvl(hier.MGR_NAME, 'Not Assigned') as MGR_NAME,
       nvl(hier.THEATER, 'Not Assigned') as THEATER,
       c.account_name,
       c.sold_as_sw_allocation,
       c.sold_as_hw_allocation
from CPS_DSCI_API.dc_BOOKINGS_CONTRACTS c
    join CPS_DSCI_API.DC_SOLD_AS_SERVICE_TYPES st on ( st.SERVICE_TYPE_ID=c.SOLD_AS_SERVICE_TYPE_ID)  -- all are mapped to at least a 1
    join CPS_DSCI_API.dc_buying_programs bp on ( bp.BUYING_PROGRAM_TYPE_ID= c.BUYING_PROGRAM_TYPE_ID)
    join CPS_DSCI_API.dc_theater t on ( t.THEATER_ID = c.BOOKED_THEATER_ID)
    join CPS_DSCI_API.dc_pricing_model pm on (pm.PRICING_type_id  = c.SOLD_AS_PRICING_TYPE_ID )
    left join so on ( c.BOOKING_CONTRACT=so.BOOKING_CONTRACT and  c.is_deleted ='F')
    left join hier on (hier.DC_USER_ID=so.DC_USER_ID )
where current_date between c.AGREEMENT_START_DATE and dateadd(month,1,c.AGREEMENT_END_DATE);


-- view 3: DC_QUALIFIED_SIGNOFF

create or replace view CPS_DB.CPS_DSCI_BR.DC_QUALIFIED_SIGNOFF(
	BOOKING_CONTRACT,
	IBV_METHOD,
	IBV_IDENTITY,
	IBV_EVENT,
	NOTES,
	QUALIFIED_IBV,
	DAYS_SINCE_LAST_SIGNOFF_EVENT,
	LAST_SIGNOFF_DATE
) as
 with so as ( -- this and qualified SO need to be crisp granularity of booking contract level across 2 events signoff and disconnect... so is it really 1?
            with mx_date as (-- resolve to tru last event
                select s.BOOKING_CONTRACT, max(s.CREATE_DTM) as last_signoff_date
                from CPS_DSCI_API.DC_WF_IB_SIGNOFF s
                group by BOOKING_CONTRACT
            ) -- get the unique last event details
            select distinct s.BOOKING_CONTRACT,
                   case
                       when s.SIGNOFF_METHOD_ID != 7 then 'Signed off'
                       when s.SIGNOFF_METHOD_ID = 7 then 'Defered Signed off'
                       else 'sign_off_overdue'
                       end           as signoff_type,
                     last_signoff_date,
                 m.SIGNOFF_METHOD as ibv_method ,
                i.SIGN_OFF_IDENTITY as ibv_identity,
              e.SIGNOFF_EVENT as ibv_event,
              s.NOTES
                from CPS_DSCI_API.DC_WF_IB_SIGNOFF s
                    join CPS_DSCI_API.DC_TYP_SIGNOFF_METHOD m on ( m.SIGNOFF_METHOD_ID=s.SIGNOFF_METHOD_ID)
                join CPS_DSCI_API.DC_TYP_SIGN_OFF_IDENTITY i on ( i.SIGN_OFF_IDENTITY_ID = s.SIGN_OFF_IDENTITY_ID)
                join CPS_DSCI_API.DC_TYP_SIGNOFF_EVENT e on ( e.SIGNOFF_EVENT_ID = s.signoff_event_id)
                join mx_date on ( mx_date.BOOKING_CONTRACT=s.BOOKING_CONTRACT and mx_date.last_signoff_date=s.CREATE_DTM)
                join CPS_DSCI_API.dc_BOOKINGS_CONTRACTS c
                          on (c.BOOKING_CONTRACT = s.BOOKING_CONTRACT and c.is_deleted = 'F')
            where current_date between c.AGREEMENT_START_DATE and dateadd(day, 30, c.AGREEMENT_END_DATE)
            and s.is_deleted = 'F'
    ) -- qualify the last event with current date for correct status
 select  distinct BOOKING_CONTRACT,ibv_method, ibv_identity,ibv_event,notes,
           case
                when DATEDIFF(day, last_signoff_date,current_date) > 90 then  'sign_off_overdue'  -- regardless of type after 90 your overdue
                else signoff_type
           end as qualified_ibv,
           DATEDIFF(day, last_signoff_date,current_date) as days_since_last_signoff_event,
           last_signoff_date
        from so;

-- view 4: CAM_ACTIVITY_NEVER_SIGNOFF
create or replace view CPS_DB.CPS_DSCI_BR.CAM_ACTIVITY_NEVER_SIGNOFF(
	BOOKING_CONTRACT,
	SOLD_AS_SERVICE_NAME,
	BOOKING_COUNTRY,
	BUYING_PROGRAM_NAME,
	PRICING_MODEL_NAME,
	BOOKED_THEATER,
	LEVEL6_CISCO_WORKER_NAME,
	LEVEL7_CISCO_WORKER_NAME,
	LEVEL8_CISCO_WORKER_NAME,
	LEVEL9_CISCO_WORKER_NAME,
	EMP_CCO_ID_MASKED,
	MGR_NAME,
	THEATER,
	ACCOUNT_NAME,
	SOLD_AS_SW_ALLOCATION,
	SOLD_AS_HW_ALLOCATION
) as
with  hier as (
            select distinct  LEVEL6_CISCO_WORKER_NAME, LEVEL7_CISCO_WORKER_NAME, LEVEL8_CISCO_WORKER_NAME,LEVEL9_CISCO_WORKER_NAME,
                u.USER_ID, h.EMP_NAME,  h.mgr_name,
                   h.emp_cco_id_masked,
                   h.dc_theater as THEATER,
                   u.USER_TITLE as ROLE,
                    u.USER_ID as DC_USER_ID
            from CPS_DSCI_API.DC_USERS u
                     left join CPS_DSCI_API.organizational_hierarchy h on (concat(h.emp_cco_id, '@cisco.com') = u.CISCO_CCO_ID)
            where u.IS_DELETED = 'F'
              and emp_cco_id_masked is not null
    )
select
    c.BOOKING_CONTRACT,
    st.SOLD_AS_SERVICE_NAME,
       c.booking_country ,
        bp.BUYING_PROGRAM_NAME,
        pm.PRICING_MODEL_NAME,
        t.THEATER_NAME as booked_theater,
       nvl(hier.LEVEL6_CISCO_WORKER_NAME, 'Not Assigned') as LEVEL6_CISCO_WORKER_NAME,
       nvl(hier.LEVEL7_CISCO_WORKER_NAME, 'Not Assigned') as LEVEL7_CISCO_WORKER_NAME,
       nvl(hier.LEVEL8_CISCO_WORKER_NAME, 'Not Assigned') as LEVEL8_CISCO_WORKER_NAME,
       nvl(hier.LEVEL9_CISCO_WORKER_NAME, 'Not Assigned') as LEVEL9_CISCO_WORKER_NAME,
       nvl(hier.emp_cco_id_masked, 'Not Assigned') as emp_cco_id_masked,
       nvl(hier.MGR_NAME, 'Not Assigned') as MGR_NAME,
       nvl(hier.THEATER, 'Not Assigned') as THEATER,
       c.account_name,
       c.sold_as_sw_allocation,
       c.sold_as_hw_allocation
from CPS_DSCI_API.dc_BOOKINGS_CONTRACTS c
    join CPS_DSCI_API.DC_SOLD_AS_SERVICE_TYPES st on ( st.SERVICE_TYPE_ID=c.SOLD_AS_SERVICE_TYPE_ID)  -- all are mapped to at least a 1
    join CPS_DSCI_API.dc_buying_programs bp on ( bp.BUYING_PROGRAM_TYPE_ID= c.BUYING_PROGRAM_TYPE_ID)
    join CPS_DSCI_API.dc_theater t on ( t.THEATER_ID = c.BOOKED_THEATER_ID)
    join CPS_DSCI_API.dc_pricing_model pm on (pm.PRICING_type_id  = c.SOLD_AS_PRICING_TYPE_ID )
    left join CPS_DSCI_API.dc_BOOKINGS_CONTRACTS_RESPONSIBLE_USERS r on ( r.BOOKING_CONTRACT=c.BOOKING_CONTRACT and  r.IS_DELETED = 'F'  )
    left join hier on (hier.DC_USER_ID=r.DC_USER_ID )
where current_date between c.AGREEMENT_START_DATE and dateadd(month,1,c.AGREEMENT_END_DATE)
and c.BOOKING_CONTRACT not in (
            select s.BOOKING_CONTRACT
            from    CPS_DSCI_API.DC_WF_IB_SIGNOFF s
            join CPS_DSCI_API.dc_typ_defer_signoff_reason sor on ( sor.DEFER_SIGNOFF_REASON_ID=s.DEFER_SIGNOFF_REASON_ID)
            join CPS_DSCI_API.DC_ENGAGEMENT_HDR e on (e.dc_engagement_id =s.dc_engagement_id)
            JOIN CPS_DSCI_API.DC_TYP_SIGNOFF_METHOD m on (m.SIGNOFF_METHOD_ID=s.SIGNOFF_METHOD_ID )
            JOIN CPS_DSCI_API.DC_TYP_SIGN_OFF_IDENTITY i on (i.SIGN_OFF_IDENTITY_ID =s.SIGN_OFF_IDENTITY_ID )
            join CPS_DSCI_API.DC_USERS u on (s.DC_USER_ID = u.USER_ID )
            join CPS_DSCI_ARCHIVE.DIM_DATE_NEW d on (d.DATE = s.CREATE_DTM::date)
            );

-- view 5 : CAM_ACTIVITY_RISK_SIGNOFF
create or replace view CPS_DB.CPS_DSCI_BR.CAM_ACTIVITY_RISK_SIGNOFF(
	BOOKING_CONTRACT,
	SOLD_AS_SERVICE_NAME,
	BOOKING_COUNTRY,
	BUYING_PROGRAM_NAME,
	PRICING_MODEL_NAME,
	BOOKED_THEATER,
	LEVEL6_CISCO_WORKER_NAME,
	LEVEL7_CISCO_WORKER_NAME,
	LEVEL8_CISCO_WORKER_NAME,
	LEVEL9_CISCO_WORKER_NAME,
	EMP_CCO_ID_MASKED,
	MGR_NAME,
	THEATER,
	ACCOUNT_NAME,
	SOLD_AS_SW_ALLOCATION,
	SOLD_AS_HW_ALLOCATION,
	SIGNOFF_DAYS_AGO,
	SIGNOFF_RISK
) as
with mx_so_per_bc as ( -- max non deferred signoff regardless of type where agreemnt > 3 month old
                     select s.BOOKING_CONTRACT, max(s.CREATE_DTM) as last_signoff_date
                      from CPS_DSCI_API.DC_WF_IB_SIGNOFF s
                               join CPS_DSCI_API.dc_BOOKINGS_CONTRACTS c
                                    on (c.BOOKING_CONTRACT = s.BOOKING_CONTRACT and c.is_deleted = 'F')
                      where current_date between dateadd(month, 3, c.AGREEMENT_START_DATE) and c.AGREEMENT_END_DATE  -- at least 90 days old
                      and s.SIGNOFF_METHOD_ID != 7 -- DEFERED
                      and s.is_deleted ='F'
                      group by s.BOOKING_CONTRACT
), hier as (
            select distinct  LEVEL6_CISCO_WORKER_NAME, LEVEL7_CISCO_WORKER_NAME, LEVEL8_CISCO_WORKER_NAME,LEVEL9_CISCO_WORKER_NAME,
                u.USER_ID, h.EMP_NAME,  h.mgr_name,
                   h.emp_cco_id_masked,
                   h.dc_theater as THEATER,
                   u.USER_TITLE as ROLE,
                    u.USER_ID as DC_USER_ID
            from CPS_DSCI_API.DC_USERS u
                     left join CPS_DSCI_API.organizational_hierarchy h on (concat(h.emp_cco_id, '@cisco.com') = u.CISCO_CCO_ID)
            where u.IS_DELETED = 'F'
              and emp_cco_id_masked is not null
), risky as (
       select
           c.BOOKING_CONTRACT,
           st.SOLD_AS_SERVICE_NAME,
       c.booking_country ,
       bp.BUYING_PROGRAM_NAME,
       pm.PRICING_MODEL_NAME,
       t.THEATER_NAME as booked_theater,
       nvl(hier.LEVEL6_CISCO_WORKER_NAME, 'Not Assigned') as LEVEL6_CISCO_WORKER_NAME,
       nvl(hier.LEVEL7_CISCO_WORKER_NAME, 'Not Assigned') as LEVEL7_CISCO_WORKER_NAME,
       nvl(hier.LEVEL8_CISCO_WORKER_NAME, 'Not Assigned') as LEVEL8_CISCO_WORKER_NAME,
       nvl(hier.LEVEL9_CISCO_WORKER_NAME, 'Not Assigned') as LEVEL9_CISCO_WORKER_NAME,
       nvl(hier.emp_cco_id_masked, 'Not Assigned') as emp_cco_id_masked,
       nvl(hier.MGR_NAME, 'Not Assigned') as MGR_NAME,
       nvl(hier.THEATER, 'Not Assigned') as THEATER,
       c.account_name,
       c.sold_as_sw_allocation,
       c.sold_as_hw_allocation,
       datediff(day, last_signoff_date, current_timestamp) as signoff_days_ago
        from mx_so_per_bc
        join CPS_DSCI_API.dc_BOOKINGS_CONTRACTS c on ( c.BOOKING_CONTRACT=mx_so_per_bc.BOOKING_CONTRACT and  c.is_deleted ='F')
        join CPS_DSCI_API.DC_SOLD_AS_SERVICE_TYPES st on ( st.SERVICE_TYPE_ID=c.SOLD_AS_SERVICE_TYPE_ID)  -- all are mapped to at least a 1
        join CPS_DSCI_API.dc_buying_programs bp on ( bp.BUYING_PROGRAM_TYPE_ID= c.BUYING_PROGRAM_TYPE_ID)
        join CPS_DSCI_API.dc_theater t on ( t.THEATER_ID = c.BOOKED_THEATER_ID)
        join CPS_DSCI_API.dc_pricing_model pm on (pm.PRICING_type_id  = c.SOLD_AS_PRICING_TYPE_ID )
        left join CPS_DSCI_API.dc_BOOKINGS_CONTRACTS_RESPONSIBLE_USERS r on ( r.BOOKING_CONTRACT=c.BOOKING_CONTRACT and  r.IS_DELETED = 'F'  )
        left join hier on (hier.DC_USER_ID=r.DC_USER_ID )
        --where signoff_days_ago > 60
        )
select *,
       case
           when signoff_days_ago between 0 and 60 then 'a_low_risk'
           when signoff_days_ago between 60 and 90 then 'b_med_risk'
           when signoff_days_ago > 90 then 'c_high_risk'
        end as signoff_risk
from risky;

