cycle_a = 10
cycle_b = 30
cycle_c = 60

poll_items = [                  # datapoints defined here will be polled, ignored if poll_list.py found in working dir
    # ([PollCycle,] Name, DpAddr, Length [, Scale/Type [, Signed]),
       # PollCycle:   Optional entry to allow the item to be polled only every x-th cycle
       # Name:        Datapoint name, published to MQTT as {dpname}
       # DpAddr:      Address used to read the datapoint value (hex with '0x' or decimal)
       # Length:      Number of bytes to read
       # Scale/Type:  Optional; if omitted, value returns as a hex byte string without '0x'. See Wiki for details
       # Signed:      Numerical data will interpreted as signed (True) or unsigned (False, default is False if not explicitly set)

########################################################################################################################################### 
#                                                                          #  HA   #  Wert # 
#  ([PollCycle,] Name, DpAddr, Len, Scale/Type, Signed)                    #[J,N,O]#  Ok?  # Kommentar / Viessmann Bezeichnung
###########################################################################################################################################
    (cycle_c,"aussentemp", 0x0101, 2, 0.1, True),                               # J     # J     # API(HA): Außentemperatur (Wert)
    ("cop", 0x1690, 1, 0.1, False),                                        # J     # J     #
    ("eheizung_betrieb", 0x7902, 1, 1, False),                             # J     # J     # Schalter fuer Durchlauferhitzer; WPR_eHeizung_Heizbetrieb_mit_Elektro
    (30,"eheizung_leistung", 0x1909, 1, 3000, False),                      # J     # J     # Aktuelle Leistung eHeizung    (30,"eheizung_leistung", 0x1909, 1, 3000, False),                      # J     # J     # Aktuelle Leistung eHeizung
    (30,"eheizung_stufe_1_betriebsstunden", 0x0588, 4, 0.0008333, False),  # J     # J     # WPR_RelaisLaufzeiten_eHeizung_Stufe1
    (30,"eheizung_stufe_2_betriebsstunden", 0x0589, 4, 0.0016667, False),  # J     # J     # WPR_RelaisLaufzeiten_eHeizung_Stufe2
    ("hk2_betriebsart", 0xB001, 1, 1, False),                              # O     # J     #
    (30,"hk2_frostschutz_allgemein", 0x1410,19,'b:2:2', 1, False),         # J     # !     # API(HA): Frostschutz (Wert)
    (30,"hk2_frostschutz_aussentemp", 0x1410,19,'b:4:4', 1, False),        # J     # !     # API(HA): Frostschutz (Wert)   
    (30,"hk2_heizkreispumpe", 0x048E, 1, 1, False),                        # J     # J     # API(HA): Heizkreisumwälzpumpe (Wert); APP: Heizkreis 2 -> Heizkreispumpe (Wert)
    (60,"hk2_heizkreispumpe_betriebsstunden", 0x058E, 4, 2.7778e-4, False),# J     # J     #
    (30,"hk2_heizkurve_neigung", 0x3007, 2, 0.1, True),                    # J     # J     # API(HA): Steigung der Heizkurve (Regler; 0-3,5; x,x)
    (30,"hk2_heizkurve_niveau", 0x3006, 2, 0.1, True),                     # J     # J     # API(HA): Verschiebung der Heizkurve (Regler; 0-40; x); APP:
    (10,"hk2_mischer_warm", 0x0600, 8, 'b:2:2', 1, False),                 # J     # J     # EINTRAGEN
    (30,"hk2_raumtemp_effektiv_soll", 0xA446, 2, 0.01, False),             # J     # J     # nvoHCC2_EffRoomSetpt
    ("hk2_raumtemp_soll", 0x3000, 2, 0.1, False),                          # J     # J     # API(HA): Normaltemperatur (Regler; 0-30; x)
    ("hk2_raumtemp_soll_party", 0x3022, 2, 0.1, False),                    # J     # J     # API(HA): Komfort Temperatur (Regler; 0-30; x)
    ("hk2_raumtemp_soll_reduziert", 0x3001, 2, 0.1, False),                # J     # J     # API(HA): Reduzierte Temperatur (Regler; 0-30; x)
    (30,"hk2_temp", 0x0117, 2, 0.1, False),                                # O     # N     # WPR_Raumtemperatur_HK_M2_Vitotrol # vermutlich Vorgabe Raumthermostat
    (10,"hk2_temp_vl", 0x0114, 2, 0.1, False),                             # J     # J     # API(HA): Vorlauftemperatur (Wert); APP: Heizkreis 2 -> Vorlauf (Wert)
    (30,"hk2_temp_vl_soll", 0x1801, 2, 0.1, False),                        # J     # J     # WPR3_Vorlaufsolltemperatur_HK2
    (30,"kk_el_expansionsventil_position", 0xB424, 2, 1, False),           # N     # J     # WPR3_B424_Position_ECV_Sensorstatus
    (30,"kk_fluessiggastemp", 0xB404, 3, 'b:0:1', 0.1, True),              # J     # J     # WPR3_Fluessiggastemperatur
    (30,"kk_heissgasdruck", 0xB411, 3, 'b:0:1', 0.1, True),                # J     # J     # WPR3_B411_Heissgasdruck_Sensorstatus
    (30,"kk_heissgastemp", 0xB40A, 3, 'b:0:1', 0.1, True),                 # J     # J     # WPR3_HEISSGAS
    (30,"kk_kondensationstemp", 0xB408, 3, 'b:0:1', 0.1, True),            # J     # J     # WPR3_KONDENSATION
    (30,"kk_leistung_vd", 0xB423, 2, 1, False),                            # J     # J     # WPR3_B423_Leistung_Verdichter
    (30,"kk_sauggasdruck", 0xB410, 3, 'b:0:1', 0.1, True),                 # J     # J     # WPR3_B410_Sauggasdruck
    (30,"kk_sauggastemp", 0xB409, 3, 'b:0:1', 0.1, True),                  # J     # J     # WPR3_SAUGGAS
    (30,"kk_ueberhitzung_soll", 0xB40B, 3, 'b:0:1', 0.1, True),            # N     # J     # WPR3_UEBERHITZUNG_SOLL_Sensorstatus
    (30,"kk_unterkuehlung_delta", 0xB40D, 3, 'b:0:1', 0.1, True),          # N     # !     # WPR3_DELTA_UNTERKUEHLUNG
    (30,"kk_verdampfungstemp_ist", 0xB407, 3, 'b:0:1', 0.1, True),         # J     # J     # WPR3_VERDAMPFUNG
    (60,"meldung_vd", 0x0708, 32),                                         # !     # ?     # Meldungen Verdichter
    (60,"meldung_vd1", 0x0704, 32),                                        # !     # ?     # Meldungen Verdichter 1
    (60,"meldung_wp", 0x0700, 32),                                         # J     # ?     # Meldungen Waermepumpenregelung
    (30,"pk_temp_vl", 0xB400, 3, 'b:0:1', 0.1, True),                      # J     # J     # API(HA): Primärkreis-Vorlauftemperatur (Wert)
    (30,"pk_ventilator", 0xB420, 2, 1, False),                             # J     # J     # WPR3_B420_Drehzahl_Primaerquelle
    ("pufferspeicher_temp", 0x010B, 2, 0.1, False),                     # J     # J     # API(HA): Puffertemperatur / Puffertemperatur oben; ; APP: Pufferspeicher -> Temperatur (+oben) Pufferspeicher (Wert)
    (3600,"scop", 0x1680, 1, 0.1, False),                                  # J     # J     # WPR_WO1H_JAZ - COP Gesamt
    (3600,"scop_hk2", 0x1681, 1, 0.1, False),                              # J     # J     #
    (3600,"scop_ww", 0x1682, 1, 0.1, False),                               # J     # J     #
    (30,"sk_pumpe", 0x0484, 1, 1, False),                                  # J     # J     # WPR_RelaisStatus_SekPumpe1
    (cycle_b,"sk_pumpe_rpm", 0xB421, 2, 1, False),                              # J     # HA    # WPR3_B421_Drehzahl_Sekundaerpumpe
    (30,"sk_temp_rl", 0xB403, 3, 'b:0:1', 0.1, True),                      # J     # J     # API(HA): Rücklauftemperatur (Wert); APP: Wärmeerzeuger -> Rücklauftemperatur
    (30,"sk_temp_vl", 0xB402, 3, 'b:0:1', 0.1, True),                      # J     # J     # API(HA): Sekundärkreis-Vorlauftemperatur (Wert)
    (3600,"vd_belastungskl_1", 0x1620, 2, 1, False),                       # J     # J     # Belastungsklassen in Stunden
    (3600,"vd_belastungskl_2", 0x1622, 2, 1, False),                       # J     # J     #
    (3600,"vd_belastungskl_3", 0x1624, 2, 1, False),                       # J     # J     #
    (3600,"vd_belastungskl_4", 0x1626, 2, 1, False),                       # J     # J     #
    (3600,"vd_belastungskl_5", 0x1628, 2, 1, False),                       # J     # J     #
    (600,"vd_betriebsstunden", 0x0580, 4, 2.7777778e-4, False),            # J     # J     # API(HA): Kompressorbetriebsstunden (Wert); APP: Verdichter -> Betriebsstunden Verdichter (Wert)
    (30,"vd_el_leistungsaufnahme", 0x16A4, 4, 1, False),                   # J     # J     # WPR3_Leistungsaufnahme_1
    (30,"vd_elektrische_energie", 0x1660, 4, 0.1, False),                  # J     # J     # WPR3_Leistungsaufnahme_2
    (30,"vd_heizleistung", 0x16A0, 4, 1, False),                           # J     # J     # WPR3_Heizleistung_1
    (3600,"vd_heizwaerme", 0x1640, 4, 0.1, False),                         # J     # J     # WPR_WO1H_Energie_Verdichter1
    (60,"vd_starts_anzahl", 0x0500, 4, 'b:0:1', 1, False),                 # J     # J     # API(HA): Kompressorstarts (Wert); APP: Verdichter -> Starts Verdichter (Wert)
    ("vd_status_abtauen", 0xB446, 1, 1, False),                            # J     # J     # WPR3_B446_Ausgang_Abtauung EINTRAGEN
    ("vd_status_betrieb", 0x0480, 1, 1, False),                            # J     # J     # API(HA): Kompressor (Wert) / Kompressorphase (Wert; ein, aus, preparing, defrost, pause); APP: Verdichter -> Verdichterstatus (Wert)
    (30,"ww_el_energie", 0x1670, 4, 0.1, False),                           # ?     # ?     #
    (30,"ww_hysterese_eheizung", 0x6008, 2, 0.1, False),                   # ?     # ?     #
    (30,"ww_hysterese_vd", 0x6007, 2, 0.1, False),                         # ?     # ?     #
    (30,"ww_speicherladepumpe", 0x0496, 1, 1, False),                      # J     # J     #
    (30,"ww_speichertemp_max", 0x6006, 2, 0.1, False),                     # ?     # ?     #
    (30,"ww_speichertemp_min", 0x6005, 2, 0.1, False),                     # ?     # ?     #
    (30,"ww_speichertemp_oben", 0x01CD, 3, 'b:0:1',0.1, True),             # J     # J     # API(HA): WW Speichertemperatur / WW Speichertemperatur oben (Wert); APP: Warmwasserbereitung -> Warmwassertemperatur / Warmwasserbereitung -> Speichertemperatur oben
    (30,"ww_speichertemp_soll_2", 0x600C, 2, 0.1, False),                  # J     # J     # API(HA): WW-Sekundärtemperatur (Regler; 0-60; x)
    (30,"ww_speichertemp_soll_normal", 0x6000, 2, 0.1, False),             # J     # J     # API(HA): WW-Temperatur (Regler; 0-60; x)
    (30,"ww_zirkulationspumpe", 0x0490, 1, 1, False),                      # J     # !     # API(HA): WW-Zirkulationspumpe (Wert); ; APP: Warmwasserbereitung -> Zirkulationspumpe
    (30,"ww_zirkulationspumpe_rpm", 0xB422, 2, 1, False),                  # J     # !     # Zeigt 100 während 0x490 aus ist -> Kann am Pumpenzeitprogramm liegen?
    (450,"systemzeit", 0x08E0, 8, 'vdatetime')
]


#    (60,"sammelstoerung", 0x0411, 1, 1, False),                            # J     # ?     # Meldungen Verdichter 1, WPR_RelaisZustand_Sammelstoerung

########## Send Commands ##########
###################################

# 0xB020 einmalig Warmwasser, laut Anleitung Wert auf 1 setzen, laut Forum ist 2 korrekt # API(HA): Einmalige Aufladung aktivieren (Button)

########## Fehlende Werte #########
###################################

# API Integration
#################
# Frostschutz
# Kompressorstatus
# Warmwasser Boiler (Thermostat) > - Betriebsmodus Warmwasser (7319) [WPR_WO1H_GueltBetriebsmodusWW~0x1185 (Int)]
# WW Aufladung (Ausser Betrieb): API(HA): WW-Aufladung (Wert)
# WW-Höchsttemperatur (60) # API(HA): WW Höchsttemperatur (Wert)   - (6000) Warmwassertemperatur-Sollwert (7142) [WPR_WW_Temp_soll~0x6000 (SInt)]
# WW-Mindestemperatur (10) # API(HA): WW Mindesttemperatur (Wert)

# API Integration - Einstellbare Werte
#########################
# Kompressorphase
# WW-Hystereseschalter aus (5,0K) # API(HA): WW-Hystereseschalter aus (Regler; 0-10; x,x)
# WW-Hystereseschalter ein (5,0K) # API(HA): WW-Hystereseschalter ein (Regler; 0-10; x,x)



# App
##################
# ; APP: Elektrische Zusatzheizung -> Heizwasserdurchlauferhitzer (Wert Ein, Aus)
# Maximale Vorlauftemperatur: ; APP: Maximale Vorlauftemperatur (Wert)
# Seriennummer ; APP: Seriennummer (Wert)
# Datum / Uhrzeit ; APP: Datum und Uhrzeit des Geräts (Wert)
# ; APP: Zustand Komponenten -> Elektrische Zusatzheizung (Wert)
# HK2 Frostschutz
   
# ????
###########
#    - Speichernachheizung (6709) [WPR_RelaisStatus_Speichernachheizung~0x048A (Byte)]
#    - Speichernachheizung (6649) [WPR_RelaisLaufzeiten_Speichernachheizung~0x058A (Int4)]

# Aus anderen Konfigs (nicht ausprobiert)
##################
#    (60, "hk2_pump_runtime", 0x058E, 4, 2.777777777777778e-4, False),
#    ("secondary_pump_runtime", 0x0584, 4, 2.777777777777778e-4, False),
#
# setHeaterforWW" protocmd="setaddrValue"> <addr>6015</addr> <len>1</len> <unit>XX</unit> <description>Druchlauferhitzer für Warmwasser aktivieren</description> </command>
#  <command name="setHeaterforRoomtemp" protocmd="setaddrValue"> <addr>7902</addr> <len>1</len> <unit>XX</unit> <description>Durchlauferhitzer für Heizung aktivieren</description> </command>
# 
#     ("WP_OptimaleLaufzeitVerdichter1 (500A)",0x500a, 2, 1),
#    ("WP_HK1_TemperaturFrostschutz (7006)", 0x7006, 2, 0.1, True),
#    ("WP_FreigabeElektroheizung (7900)", 0x7900, 1, 1), #Grundeinstellung ElektroHeizung, hiervon abhängig 7902 und 6015
#    ("WP_ElektroZusatzHeizungEin (7902)",0x7902, 1, 1),
#    ("WP_WW_FreigabeElektroheizung (6015)",0x6015,1,1),

# Backup / Alternativen (Gestestet)
##################
#    (10,"hk2_temp_vl", 0x01D4, 3, 'b:0:1', 0.1, False),                   # J     # J     # WPR3_Vorlauftemp_HK2 0x0114

# Vitogate EIB (Länge 1 Byte)
##################
#                   # hex - dez
#Abschaltbetrieb    # 0x00 - 0
#Warmwasser         # 0x01 - 1
#Heizen und Warmwasser #0x02 - 2
#dauernd reduziert  # 0x04 - 4
#dauernd normal     # 0x05 - 5
#normal Abschalt    # 0x06 - 6
#nur Kühlen         # 0x07 - 7
#Partybetrieb
#                   # hex - dez
#Partybetrieb aus   # 0x00 - 0
#Partybetrieb ein   # 0x01 - 1

