ASG(default) {
    INPA($(P)ReadOnly)
    RULE(1, READ)
    RULE(1, WRITE){
        CALC("A<1")
    }
}