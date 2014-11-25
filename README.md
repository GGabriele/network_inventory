network_inventory
=================

This script connect to each node of the network using PExpect.
Then we'll filter command outputs using regular expressions and lastly, 
we'll store these filtered output into the "net_invent.txt" file.

Informations we'll obtain:
- Router_ID
- RAM Memory
- Flash Memory
- Free Flash
- IOS Version
- Linecards
- Serial numbers
