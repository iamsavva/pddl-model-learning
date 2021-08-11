(:predicates 
  (IsObject ?obj )
  (IsArm ?obj)
  (IsBlock ?obj)   ;             is a block
  (IsConf ?q)       ;             is a configuration

  (KinMove ?q ?p)
  (KinPick ?q ?p)
  (Pos ?b ?p) ;     block b is at pose p
  (Conf ?arm ?q)       ;     arm at configuration
  (Holding ?arm ?b) ;          holding a block
  (ArmEmpty ?arm) ;           holding nothing
  (Movable ?obj)
)

