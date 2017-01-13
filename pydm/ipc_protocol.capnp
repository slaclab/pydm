@0xb4020e7ba1433510;

struct ClientMessage {
  union {
    initialize @0 :InitializeConnectionMessage;
    channelRequest @1 :Text;
    channelDisconnect @2 :Text;
    newWindowRequest @3 :NewWindowRequestMessage;
    putRequest @4 :PutRequestMessage;
  }
}

struct InitializeConnectionMessage {
  clientPid @0 :Int32;
}

struct NewWindowRequestMessage {
  filename @0 :Text;
}

struct PutRequestMessage {
  channelName @0 :Text;
  value @1 :ValueMessage;
}

struct ServerMessage {
  channelName @0 :Text;
  union {
    value @1 :ValueMessage;
    connectionState @2 :Bool;
    severity @3 :AlarmSeverity;
    writeAccess @4 :Bool;
    enumStrings @5 :List(Text);
    unit @6 :Text;
    precision @7 :Int8;
  }
  enum AlarmSeverity {
    noAlarm @0;
    minor @1;
    major @2;
    invalid @3;
    disconnected @4;
  }
  timestamp @8 :Float64;
}

struct ValueMessage {
  value :union {
    string @0 :Text;
    int @1 :Int64;
    float @2 :Float32;
    double @3 :Float64;
    char @4 :Data;
    intWaveform @5 :List(Int64);
    floatWaveform @6 :List(Float64);
    charWaveform @7 :List(Data);
  }
}