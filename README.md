# qcells-modbus-tools
Some tools for QCells Inverter, modbus, mqtt, Shelly 3empro, Marstek Venus 3 and Home Assistant

Diese Sammlung an tools benötige ich für meine PV Anlage, die aus einem QCells Q.Volt P5T besteht, der mit einem DTSU666 über modbus rtu kommuniziert und die Energie-Daten in die Cloud läd.

Dazu habe ich mir nach gut einem Jahr einen Akku Marstek Venus V3 gekauft, da meine Verbrauchdaten gezeigt haben, dass ich ihn gut 300 Zyklen laden kann. In Verbindung mit unserem Strompreis von 0.35 € sollte er sich im schlechtesten Fall in gut 3.5 Jahren amortisieren.

Um alle Geräte in den Home Assistant zu integrieren, war allerdings etwas Recherche und Programmierung angesagt, da mein HA nicht im Keller neben dem WR steht. Dafür steht dort unser Home-Server, mit dem ich auf alle Geräte zugreifen und die Daten an den HA weiterreichen kann.

Folgende Tools benötige ich dazu:
1. [Modbus Bridge from rtu to tcp](docs/modbus-bridge.md)
2. [DTSU666 modbus reader](docs/dtsu666-reader.md)
3. Mqtt bridge for the dtsu666
4. Shelly 3em pro adapter for the Marstek Akku to get the energy data from the dtsu666

Alle Tools können auch mehr oder weniger einzeln benutzt werden.

Die config umfasst alle Tools, da ich alle benötige. Das logging level ist zentral
und gilt für alle Tools gemeinsam.


## 3. Mqtt-Bridge