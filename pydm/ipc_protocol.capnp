@0xb4020e7ba1433510;

struct Message {
  union {
    data @0 :NewDataMessage;
    channelRequest @1 :Text;
    channelDisconnect @2 :Text;
    newWindowRequest @3 :NewWindowRequestMessage;
    initialize @4 :InitializeConnectionMessage;
  }
}

struct InitializeConnectionMessage {
  clientPid @0 :Int32;
}

struct NewDataMessage {
  channelName @0 :Text;
  value :union {
    string @1 :Text;
    int @2 :Int32;
    float @3 :Float32;
    double @4 :Float64;
    char @5 :Data;
    intWaveform @6 :List(Int32);
    floatWaveform @7 :List(Float32);
    doubleWaveform @8 :List(Float64);
    charWaveform @9 :List(Data);
  }
  severity @10 :AlarmSeverity;
  enum AlarmSeverity {
    noAlarm @0;
    minor @1;
    major @2;
    invalid @3;
    disconnected @4;
  }
  timestamp @11 :Int32;
  units @12 :Text;
}

struct ChannelRequestMessage {
  channelName @0 :Text;
}

struct ChannelDisconnectMessage {
  channelName @0 :Text;
}

struct NewWindowRequestMessage {
  filename @0 :Text;
}

