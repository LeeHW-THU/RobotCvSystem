package cn.huww98.picontroller

import com.fasterxml.jackson.annotation.JsonTypeInfo
import com.fasterxml.jackson.annotation.JsonTypeName
import com.fasterxml.jackson.annotation.JsonValue

interface IControlCommand

object StopCommand : IControlCommand {
    @JsonValue
    fun getJson() = "Stop"
}

@JsonTypeName("power")
@JsonTypeInfo(include = JsonTypeInfo.As.WRAPPER_OBJECT, use = JsonTypeInfo.Id.NAME)
data class PowerCommand(
    val left: Double,
    val right: Double
) : IControlCommand {
}
