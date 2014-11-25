import pexpect
import re
_USERNAME = 'cisco' 
_PASSWORD = 'cisco' 


class Router(object):

''' 
We'll connect to each node of the network using PExpect.
Then we'll filter command outputs using regular expressions and lastly, 
we'll store these filtered output into the "net_invent.txt" file.

Informations we'll obtain:
	- Router_ID
	- RAM Memory
	- Flash Memory
	- IOS Version
	- Linecards
	- Serial numbers
'''


    network_nodes = {}    # We'll store here couples Router_ID : IP_address.
    diagram = {}
    f = open('Routers.txt', 'r')					         


    for line in f:
        list = line.split()
        diz[list[0]] = list[1]

    print network_nodes
    f.close()


    def check_version(command):
        child.sendline(command)
        child.sendline()
        child.expect (router+'>', timeout = 30)
        output_version = child.before.split()
        print "CHILD BEFORE: ", child.before

        filter_version = re.findall("\(C.+\)", child.before)
        final_filter_version = re.sub("(RELEASE.*) \(f.+\)", " ", str(filter_version)).replace(",", " ").replace("[", " ").replace("]", " ").replace("'", "")
        print "FINAL FILTER_VERSION: ", final_filter_version
        final = "Router ID: %s \n\t Software: %s \n" % (router, final_filter_version)
        inventory.write(final)
        return final_filter_version


    def check_model(command):
        child.sendline(command)
        child.expect (router+'>')
        output_model = child.before
        filter_model = re.findall("Cisco ([0-9]+)", output_model)
        model = re.sub("[\[\]']", "", str(filter_model))
        print "FILTER_MODEL: ", model
        inventory.write("\tHardware Model: Cisco %s\n" % model)
        return model


    def check_memory(command):
        child.sendline(command)
        child.expect (router+'>')
        output_memory = child.before
        filter_main_memory = re.findall("([0-9]+K/)", output_memory)
        filter_shared_memory = re.findall("(/[0-9]+)", output_memory)
        shared_memory = re.sub("[\[\]\(\)',K/]", "", str(filter_shared_memory))
        main_memory = re.sub("[\[\]\(\)',K/]", "", str(filter_main_memory))
        print "Main Memory: ", main_memory
        print shared_memory
        total_memory = int(main_memory) + int(shared_memory)
        print "MEMORY: ", total_memory
        inventory.write("\tRAM Memory: %s\n" % total_memory)
        return total_memory


    def check_flash(command):
        child.sendline(command)
        child.expect (router+'>')
        output_flash = child.before
        filter_flash = re.findall("([0-9]+)", output_flash)
        flash = re.sub("[\[\]']", "", str(filter_flash))
        print "FLASH: ", flash
        inventory.write("\tFlash memory: %s\n" % flash)
        return flash


    def check_free_flash(command):
        child.sendline("enable")
        child.expect("Password: ")
        child.sendline (_PASSWORD)
        child.expect (router+'#')
        child.sendline(command)
        child.expect (router+'#')
        output_free_flash = child.before
        child.sendline ('disable')
        child.expect (router+'>')
        filter_free_flash = re.findall("([0-9]+(\s+)bytes(\s+)free)", output_free_flash)
        free_flash = re.sub("[\[\]'\(\),]", "", str(filter_free_flash))
        print "FREE FLASH: ", free_flash
        inventory.write("\tFlash memory: %s\n" % free_flash)
        return free_flash


    def check_line_cards(command):

        '''
        First, we have to know how many linecards exist inside our device. The "max_slot" variable will 
        contain this number. Then, we'll need to iterate the "show diag" for every linecards
        print "CHILD: ", child.before
        ''' 

        slots = {}

        child.sendline(command)
        child.expect (router+'>sh diag')
        output_diag = child.before
        # print "OUT: ", output_diag
        filter_diag = re.findall("([0-9]+)-([0-9]+)", output_diag)
        diag = re.sub("[\[\]\(\)',]", "", str(filter_diag))
        # print "DIAG: ", diag
        list = diag.split()
        max_slot = int(list[-1])
        # print "MAX_SLOT: ", max_slot
        child.sendline('exit')


        for i in range(0, max_slot+1):
            # print "CHILD_BEFORE: ", child.before
            command_slot = 'sh diag %d | include port' % i
            # print "COMMAND:", command
            child = pexpect.spawn('telnet ' + ip_address )
            child.expect ('Username: ')
            child.sendline (_USERNAME)
            child.expect("Password: ")
            child.sendline(_PASSWORD)
            child.expect (router+'>')
            child.sendline(include_port)
            child.expect (router + '>')
            output_slot = child.before
            print "OUTPUT_SLOT: ", output_slot
            filter_command_slot = 'sh diag %d \| include port' % i
            slot = re.sub(filter_command_slot, "", str(output_slot))
            inventory.write("\tSLOT %d" % i)
            inventory.write("\t" + slot)


            command_serial = 'show diag %d | include Serial' %i
            child.sendline(command)
            child.expect (router+'>')
            output_serial = child.before
            filter_command_serial = 'show diag %d \| include Serial' %i
            serial = re.sub(filter_command_serial, "", str(output_serial))
            inventory.write("\t" + serial)

            port = slot + serial
            slots["Slot %d" % i] = meh.replace('\r\n\t', " ").replace('\r\n\r\n\t', " ").replace('\t', " ").replace('\r\n', "")
            return slots



    def launch():

        inventory = open('net_invent', 'a')
        
        for router in network_nodes:

            print 'Router: %s' % router
            ip_address = diz[router]
            print 'ip_address: %s' % ip_address
            child = pexpect.spawn('telnet ' + ip_address )
            child.expect ('Username: ')
            child.sendline (_USERNAME)
            child.expect('Password: ')
            child.sendline(_PASSWORD)
            child.expect (router+'>')


            # VERSION

            send   = 'sh version | exclude ^$'
            verion = check_version(send)

            # MODEL

            send  = 'sh ver | sec include processor'
            model = check_model(send)

            # RAM

            send   = 'sh ver | sec include memory'
            memory = check_memory(send)

            # FLASH

            send  = 'sh ver | sec include flash'
            flash = check_flash(send)

            # FREE FLASH

            send       = 'dir flash:'
            free_flash = check_free_flash(send)


            # LINECARDS AND SN

            send = 'sh diag ?'
            linecard = check_line_cards(send)


            diagram[router] = {
                "Model: "      : model,
                "Version: "    : version,
                "RAM: "        : memory,
                "Flash: "      : flash,
                "Free Flash: " : free_flash
                "Linecards: "  : linecard
            }

            print diagram
        

        inventory.close()
