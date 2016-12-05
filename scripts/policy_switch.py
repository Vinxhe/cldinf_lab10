from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp

class SimpleHub(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	addresses = { }

	def __init__(self, *args, **kwargs):
		super(SimpleHub, self).__init__(*args, **kwargs)
		self.mac_to_port = {}
		self.define_addresses()

	def define_addresses(self):
		self.addresses['00:00:00:00:00:01'] = ['00:00:00:00:00:01', '00:00:00:00:00:02', '00:00:00:00:00:03', '00:00:00:00:00:04']
		self.addresses['00:00:00:00:00:02'] = ['00:00:00:00:00:01', '00:00:00:00:00:02', '00:00:00:00:00:03', '00:00:00:00:00:04']
		self.addresses['00:00:00:00:00:03'] = ['00:00:00:00:00:01', '00:00:00:00:00:02', '00:00:00:00:00:03', '00:00:00:00:00:04', "00:00:00:00:00:05", '00:00:00:00:00:06']
		self.addresses['00:00:00:00:00:04'] = ['00:00:00:00:00:01', '00:00:00:00:00:02', '00:00:00:00:00:03', '00:00:00:00:00:04', '00:00:00:00:00:05', '00:00:00:00:00:06']
		self.addresses['00:00:00:00:00:05'] = ['00:00:00:00:00:03', '00:00:00:00:00:04', '00:00:00:00:00:05', '00:00:00:00:00:06']
		self.addresses['00:00:00:00:00:06'] = ['00:00:00:00:00:03', '00:00:00:00:00:04', '00:00:00:00:00:05', '00:00:00:00:06']            

	@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
	def switch_features_handler(self, ev):
		datapath = ev.msg.datapath
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		match = parser.OFPMatch()
		actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
		self.add_flow(datapath, 0, match, actions)

	def add_flow(self, datapath, priority, match, actions):
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
		mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, instructions=inst)
		datapath.send_msg(mod)

	@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
	def _packet_in_handler(self, ev):
		msg = ev.msg
		datapath = msg.datapath
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser

		dpid = datapath.id
		self.mac_to_port.setdefault(dpid, {})

		pkt = packet.Packet(msg.data)
		eth_pkt = pkt.get_protocol(ethernet.ethernet)
		dst = eth_pkt.dst
		src = eth_pkt.src
		arp_pkt = pkt.get_protocol(arp.arp)

		in_port = msg.match['in_port']

		self.mac_to_port[dpid][src] = in_port

		actions = []
		out_port = ""
		if dst in self.addresses[src] and dst in self.mac_to_port[dpid]:
			out_port = self.mac_to_port[dpid][dst]
			actions = [parser.OFPActionOutput(out_port)]
			match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
			self.add_flow(datapath, 1, match, actions)
			self.logger.info("*** %s: Port %s --> %s: Port %s ***", src, in_port, dst, out_port)
		elif dst == "ff:ff:ff:ff:ff:ff" and arp_pkt:
			out_port = ofproto.OFPP_FLOOD
			actions = [parser.OFPActionOutput(out_port)]
			match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_type=0x0806)
			self.add_flow(datapath, 1, match, actions)
			self.logger.info("*** %s: Port %s --> ARP-Packet: Flood ***", src, in_port)
		elif dst not in self.addresses[src]:
			match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
			self.add_flow(datapath, 1, match, actions)
		else:
			self.logger.info("no new flow")

		out = parser.OFPPacketOut(datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER, in_port=in_port, actions=actions, data=msg.data)
		datapath.send_msg(out)

