#cldinf_lab10

Repo includes 4 scripts that implement different kinds of switches:

##simple_hub.py:
Starts a controller that floods the incoming packets to all the connected switches. All the packets are sent to the hub, no flows are written.

Start and test with the following commands:

Start the docker container (replace <username> with your username)
`docker run -ti -p 6633:6633 -v /home/<username>/my:/opt/ryu/ryu/app/my hsrnetwork/ryu bash`
Start the controller
`ryu-manager ./ryu/app/my/simple_hub.py`
Start the mininet
`mn --mac --controller remote,ip=127.0.0.1` (creates a topology with 1 switch and 2 hosts) 
test the connectivity eg. with `pingall`
expected output:
`mininet> pingall`
`*** Ping: testing ping reachability`
`h1 -> h2` 
`h2 -> h1` 
`*** Results: 0% dropped (2/2 received)`
In the terminal in which you started the controller, you should be able to see that the controller floods the packets on every port on every incoming packet

##simple_hub_2.py
Starts a controller that writes the same flow to all the switch. The flow tells all the switches to flood all packets. Only the first packets are sent to the controller. After that the switches do the flooding themselves until the flow times out.

Start and test with the same commands as with simple_hub.py.
Start the controller:
`ryu-manager ./ryu/app/my/simple_hub_2.py`
Pings should also look the same.

In the terminal in which you started the controller you should be able to see that the controller only gets the first packets. After that the switches flood the traffic by themselves.

##switch.py
Starts a controller that maps the source and destination mac-adresses of incoming packets to its corresponding ports in its mac-table and writes down the resulting flows on the switches. Its basically an implementation of a standard learning switch.

Start the docker container as before.
Start the controller:
`ryu-manager ./ryu/app/my/switch.py`
Start a bigger mininet to better observe the controller behaviour:
`sudo mn --topo=single,6 --mac --controller remote,ip=127.0.0.1`
Test with `pingall`
`mininet> pingall`
`*** Ping: testing ping reachability`
`h1 -> h2 h3 h4 h5 h6` 
`h2 -> h1 h3 h4 h5 h6`
`h3 -> h1 h2 h4 h5 h6` 
`h4 -> h1 h2 h3 h5 h6` 
`h5 -> h1 h2 h3 h4 h6` 
`h6 -> h1 h2 h3 h4 h5` 
`*** Results: 0% dropped (30/30 received)`

You will see packets on the controller until he has learned all the mac-addresses. After that the switches switch by themselves until the flows time out.

##policy_switch.py
Starts a controller that has the same properties as the one before plus it constricts access of the hosts. Host1 and host2 will not have access to the DB (host5 and host6) and host5 and host6 will not have access to the Web (host1 and host2), while host3 and host4 (App) have access to all the areas.

Start the docker container and the mininet as before.
Start the controller:
`ryu-manager ./ryu/app/my/policy_switch.py`
Test with `pingall`
mininet> pingall
`*** Ping: testing ping reachability
`h1 -> h2 h3 h4 X X` 
`h2 -> h1 h3 h4 X X` 
`h3 -> h1 h2 h4 h5 h6` 
`h4 -> h1 h2 h3 h5 h6` 
`h5 -> X X h3 h4 h6` 
`h6 -> X X h3 h4 h5` 
*** Results: 26% dropped (22/30 received)

In the terminal you will see which packet arrived on which port, from which mac-address, and on which port it was sent out to which mac-address. It will also create an output when an ARP-packet is received, which it floods to all the switches. Once all the flows are written no more outputs will be generated.


 
