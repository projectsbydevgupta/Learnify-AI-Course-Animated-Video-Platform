DOCUMENTS = [
    {
        "document": "cn_reference_models_in_computer_networks.pdf",
        "topic": "Computer Networks",
        "section": "OSI & TCP/IP Reference Models",
        "pages": [
            {
                "page": 1,
                "text": """Reference Models in Computer Networks:
In early networking, disparate hardware and software specifications made communication impossible between heterogeneous vendors.
The International Organization for Standardization (ISO) created the Open Systems Interconnection (OSI) reference model to standardize protocols and enable multi-vendor interoperability.
The two dominant reference models are:
1. OSI Reference Model (7 Layers)
2. TCP/IP Reference Model (4/5 Layers)
Introduction to ISO-OSI Model:
Developed by ISO in 1984, the OSI model divides communication tasks into 7 distinct, self-contained layers."""
            },
            {
                "page": 2,
                "text": """Seven Layers of the OSI Model:
1. Physical Layer (Hardware link, raw bit stream transmission)
2. Data Link Layer (Frames, node-to-node hop delivery, error control)
3. Network Layer (Packets, end-to-end host routing, IP addressing)
4. Transport Layer (Segments, process-to-process port delivery, reliability)
5. Session Layer (Dialog control, session synchronization checkpoints)
6. Presentation Layer (Data translation, syntax, encryption, compression)
7. Application Layer (User-facing network application protocols)"""
            },
            {
                "page": 3,
                "text": """Introduction to TCP/IP Reference Model:
Transmission Control Protocol / Internet Protocol (TCP/IP) suite was developed prior to OSI by DARPA.
It structures internetworking into 4 core layers:
1. Network Access Layer (combines OSI Physical and Data Link layers)
2. Internet Layer (IP, ICMP, ARP routing)
3. Transport Layer (TCP connection-oriented, UDP connectionless)
4. Application Layer (combines OSI Session, Presentation, Application layers: HTTP, DNS, SMTP, FTP)"""
            },
            {
                "page": 4,
                "text": """Characteristics of the OSI Model:
- Upper Layers (Application, Presentation, Session): Implemented in software; deal with user application and session representation.
- Lower Layers (Transport, Network, Data Link, Physical): Deal with data transport issues. Transport handles end-to-end reliability; Data Link and Physical are implemented in network interface hardware/drivers."""
            },
            {
                "page": 5,
                "text": """Physical Layer Deep Dive:
Primary Function: Transmit raw bit streams over physical transmission medium.
Functions:
- Line Configuration: Simplex, half-duplex, or full-duplex transmission modes.
- Physical Topology: Mesh, Star, Bus, Ring topologies.
- Signal Encoding: Digital and analog modulation across copper, fiber, or wireless RF."""
            },
            {
                "page": 6,
                "text": """Data Link Layer Deep Dive:
Primary Function: Error-free transmission of data frames across a single hop or local network.
Divided into two sub-layers:
1. Logical Link Control (LLC): Multiplexes network layer protocols, provides flow control.
2. Media Access Control (MAC): Manages access to shared physical media, encodes 48-bit MAC addresses."""
            },
            {
                "page": 7,
                "text": """Functions of Data Link Layer:
- Framing: Encapsulates network layer packets into frames with header and trailer.
- Physical Addressing: Source and destination MAC hardware addresses.
- Flow Control: Prevents fast sender from overwhelming slow receiver buffer.
- Error Control: Cyclic Redundancy Check (CRC) in frame trailer detects bit corruption; corrupted frames are dropped or retransmitted.
- Access Control: CSMA/CD or CSMA/CA protocols resolve collisions on shared channels."""
            },
            {
                "page": 8,
                "text": """Network Layer Deep Dive:
Primary Function: Host-to-host packet routing across multiple interconnected networks.
Functions:
- Logical Addressing: 32-bit IPv4 and 128-bit IPv6 addresses uniquely identify hosts globally.
- Routing: Routers select optimal paths using routing algorithms (OSPF, BGP, Dijkstra).
- Packetizing: Encapsulates transport segments into IP datagrams."""
            },
            {
                "page": 9,
                "text": """Transport Layer Deep Dive:
Primary Function: Process-to-process delivery of messages using 16-bit Port Numbers.
Two core protocols:
1. Transmission Control Protocol (TCP): Connection-oriented, reliable, guarantees in-order delivery via sequence numbers and acknowledgments, flow control via sliding windows.
2. User Datagram Protocol (UDP): Connectionless, lightweight, unreliable best-effort transport without acknowledgments or flow control."""
            },
            {
                "page": 10,
                "text": """Functions of Transport Layer:
- Service-Point (Port) Addressing: Multiplexes concurrent socket processes on a single host IP (e.g. Port 80 HTTP, Port 443 HTTPS).
- Segmentation and Reassembly: Breaks application messages into segments with sequence numbers, reassembling them at destination.
- Connection Control: 3-way handshake setup and 4-way teardown.
- End-to-End Flow & Error Control: Cumulative ACK numbers ensure missing packets are retransmitted."""
            },
            {
                "page": 11,
                "text": """Session Layer Deep Dive:
Primary Function: Establishes, maintains, and synchronizes dialog between communicating applications.
Functions:
- Dialog Control: Manages whether communication is half-duplex or full-duplex.
- Synchronization & Checkpoints: Inserts checkpoints into long data streams; if a network failure occurs, transmission resumes from the last checkpoint."""
            },
            {
                "page": 12,
                "text": """Presentation Layer Deep Dive:
Primary Function: Syntax and semantics of exchanged data (Data Translator).
Functions:
- Translation: Converts between differing encoding standards (ASCII, Unicode, EBCDIC).
- Encryption & Decryption: Cryptographic protection for privacy (SSL/TLS).
- Data Compression: Reduces bit count for audio, video, and text transmission."""
            },
            {
                "page": 13,
                "text": """Application Layer Deep Dive:
Primary Function: Serves as the window for end-user applications to access network services.
Functions:
- File Transfer, Access, and Management (FTAM / FTP).
- Mail Services (SMTP, IMAP, POP3).
- Directory Services (DNS, LDAP)."""
            },
            {
                "page": 14,
                "text": """TCP/IP Protocol Suite Architecture:
- Application Layer: HTTP, SMTP, FTP, Telnet, DNS, SNMP.
- Transport Layer: TCP, UDP.
- Internet Layer: IP, ICMP (error reporting), IGMP (multicast), ARP (address resolution), RARP.
- Network Access Layer: Ethernet, Wi-Fi 802.11, Token Ring, Frame Relay."""
            },
            {
                "page": 15,
                "text": """Internet Layer Core Protocols:
1. IP (Internet Protocol): Connectionless datagram service, MTU fragmentation and reassembly.
2. ARP (Address Resolution Protocol): Resolves logical 32-bit IP addresses to physical 48-bit MAC addresses.
   - ARP Request: Broadcasted across local LAN.
   - ARP Reply: Unicast response from target host caching MAC address."""
            },
            {
                "page": 16,
                "text": """ICMP Protocol (Internet Control Message Protocol):
Used by routers and hosts to report datagram delivery errors back to source.
- ICMP Echo Request / Reply: Powers the `ping` utility to verify reachability and RTT latency.
- ICMP Destination Unreachable / Time Exceeded: Powers `traceroute` via TTL expiration."""
            },
            {
                "page": 17,
                "text": """UDP vs TCP Header Specification:
User Datagram Protocol (UDP) Header: Minimal 8 bytes total:
- Source Port (16 bits)
- Destination Port (16 bits)
- Length (16 bits)
- Checksum (16 bits)
TCP Header: 20 to 60 bytes containing Sequence Number, ACK Number, Data Offset, Flags (SYN, ACK, FIN, RST, PSH, URG), Window Size (Flow Control), and Checksum."""
            },
            {
                "page": 18,
                "text": """Application Protocols Summary:
- HTTP / HTTPS: Web document transfer over TCP port 80 / 443.
- DNS: Domain name resolution over UDP port 53.
- SMTP: Simple Mail Transfer Protocol over TCP port 25.
- SNMP: Simple Network Management Protocol over UDP port 161."""
            }
        ]
    },
    {
        "document": "cn_tcp_handshake_snmp_packet_capture.pdf",
        "topic": "Computer Networks",
        "section": "Transport Mechanics, Management & Analysis",
        "pages": [
            {
                "page": 1,
                "text": """Chapter 10: TCP/IP Transport 3-Way Handshake (Jeff Brown):
The TCP 3-Way Handshake (SYN, SYN-ACK, ACK) is the method used by TCP to establish a reliable connection over an IP network.
Three messages are transmitted to negotiate socket parameters before transmitting application data (e.g. HTTP, SSH):
1. Host A sends SYNchronize packet to Host B (sets SYN bit = 1, chooses initial sequence number ISN_A).
2. Host B receives SYN, responds with SYN-ACK (sets SYN = 1, ACK = 1, ACK number = ISN_A + 1, chooses ISN_B).
3. Host A sends ACKnowledge (sets ACK = 1, ACK number = ISN_B + 1).
Connection is now ESTABLISHED."""
            },
            {
                "page": 2,
                "text": """TCP Connection Teardown & Reliability:
When communication concludes, a coordinated 4-way teardown is performed using FIN and ACK flags.
TCP qualifies as a reliable protocol because it tracks sequence numbers, reorders out-of-order packets, acknowledges delivery, and retransmits lost segments.
UDP is connectionless: transmits datagrams without handshake negotiation or retransmission guarantees."""
            },
            {
                "page": 3,
                "text": """Simple Network Management Protocol (SNMP):
Internet-standard protocol (IETF) for managing and monitoring devices on IP networks (routers, switches, servers, printers).
Three core components:
1. Managed Device: Node running SNMP interface.
2. SNMP Agent: Software module on managed device exposing variables.
3. Network Management System (NMS): Software console executing management queries.
Management Information Bases (MIBs): Hierarchical database describing accessible device variables using Object Identifiers (OIDs)."""
            },
            {
                "page": 4,
                "text": """SNMP Protocol Details:
Operates at Layer 7 (Application Layer).
Transport: Uses UDP port 161 for requests (GetRequest, SetRequest) and UDP port 162 for asynchronous alert notifications (Traps / InformRequests).
Versions: SNMPv1, SNMPv2c (GetBulkRequest), and SNMPv3 (cryptographic authentication and privacy encryption via USM)."""
            },
            {
                "page": 5,
                "text": """Analyzing Protocols in Packet Capture:
Packet Sniffers / Protocol Analyzers (Wireshark, tcpdump): Intercept and log traffic traversing a network interface, decoding raw headers against RFC specifications.
Capture Modes:
- Promiscuous Mode: Configures wired NIC to capture all passing frames on a broadcast domain, not just frames destined for its own MAC address.
- Monitor Mode: Wireless NIC mode capturing all 802.11 frames on a channel without associating with an Access Point."""
            },
            {
                "page": 6,
                "text": """Network Monitoring Infrastructure:
On switched networks, unicast packets are isolated to specific ports. To capture traffic, network engineers use:
- Port Mirroring (SPAN port): Switch mirrors all traffic from target ports to the analyzer port.
- Network TAPs (Test Access Points): Hardware splitters inserted directly into cabling to capture line-rate traffic without packet loss."""
            }
        ]
    }
]
