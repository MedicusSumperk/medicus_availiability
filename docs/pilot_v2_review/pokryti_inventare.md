# Pokrytí původního inventáře

Každý z původních 40 bodů má klientskou otázku, již potvrzené pracovní pravidlo, explicitní vyloučení nebo technické ověření. Nejde o důkaz implementace. Starší otevřené texty v rules.json číst spolu s pozdějšími USER-REVIEW; konsolidovaný návrh sjednocuje současný výklad.

| ID | Oblast | Kam bod patří |
| --- | --- | --- |
| MAP-01 | database_identity | Q05 Q11; oddělené identity obou DB ověří technik |
| MAP-02 | service_skin | Q04; R03 |
| MAP-03 | service_dermatoscope_first | Q01 Q02 Q03 Q04; R03 R05 |
| MAP-04 | service_followup | Q03 Q04 Q10; R03 R12 |
| MAP-05 | service_regular_check | Q04 Q10 Q12; R03 R12 |
| MAP-06 | service_plasma | Mimo první scope; R04, návrh zachovává vyloučení |
| MAP-07 | service_laser | Mimo první scope; R04, návrh zachovává vyloučení |
| MAP-08 | service_reservation | Q08 Q09; vazby ověří technik |
| MAP-09 | activity_and_type | Q04 Q08; hodnoty aktivit přiřadí technik |
| MAP-10 | doctor_identity | Q06 |
| MAP-11 | doctor_aliases | Q06; při konfliktním ID/jménu návrh odmítnout nejednoznačný filtr |
| MAP-12 | doctor_eligibility | Q06; R07 |
| MAP-13 | workplaces | Q05 |
| MAP-14 | scan_calendar | Q05 |
| MAP-15 | duration | Q01 |
| MAP-16 | scan_intervals_buffers | Q01 Q02 |
| MAP-17 | schedule_boundaries | Q02 Q08; nepřekračovat blok bez potvrzené výjimky |
| MAP-18 | overlap | Q01 Q08; technik ověří intervalové hranice a přesnost |
| MAP-19 | recurrence | Q07 Q08 Q09 |
| MAP-20 | schedule_exceptions | Q07 |
| MAP-21 | schedule_week_type | Q07; kódy týdne odvodí technik z ukázky a DB |
| MAP-22 | blocking_activities | Q04 Q05 Q08 |
| MAP-23 | resource_capacity | Q05; jeden přístroj potvrzen |
| MAP-24 | time_past | R09; technický default času v konsolidaci |
| MAP-25 | arrival_buckets | Q02; R11 |
| MAP-26 | emergency | Q13 |
| MAP-27 | search_window | Q07 Q12; R07 až R12 |
| MAP-28 | create_semantics | Q04 Q09 Q16; R17 R18 R21 |
| MAP-29 | reschedule_semantics | Q09 Q16; R16 R19 R20 |
| MAP-30 | cancel_semantics | Q09 Q16; R16 R19 |
| MAP-31 | original_appointment | Q09; R16; skutečné párování ověří technik |
| MAP-32 | patient_identity | Q10 Q11; R13 až R15 |
| MAP-33 | patient_cross_database | Q11 |
| MAP-34 | confirmation | Q16 Q18; R17 R18 R21 |
| MAP-35 | staff_intervention | Q13 až Q18; R02 R22 až R24 |
| MAP-36 | october7_evidence | Technický regresní případ 7.10.; porovnání odpovídajícího UI dle Q05 a T03 |
| MAP-37 | source_precedence | Q06 Q15 Q16; verze pravidel a nasazení řeší technik |
| MAP-38 | offer_binding | Q16; neměnné nabídky v konsolidaci, technická etapa4 |
| MAP-39 | manual_concurrency_and_holds | Q09 Q16 Q18; dočasné blokace, ruční souběh a zotavení řeší technik |
| MAP-40 | invalid_intervals | Q08; nejasné intervaly neignorovat |
