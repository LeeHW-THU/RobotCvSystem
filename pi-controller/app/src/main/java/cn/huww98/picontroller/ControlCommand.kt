package cn.huww98.picontroller

import com.fasterxml.jackson.annotation.JsonTypeInfo
import com.fasterxml.jackson.annotation.JsonTypeName
import com.fasterxml.jackson.annotation.JsonValue
import com.fasterxml.jackson.core.JsonGenerator
import com.fasterxml.jackson.databind.JsonSerializer
import com.fasterxml.jackson.databind.SerializerProvider
import com.fasterxml.jackson.databind.annotation.JsonSerialize


interface IControlCommand

object StopCommand : IControlCommand {
    @JsonValue
    fun getJson() = "Stop"
}

class RoundSerializer : JsonSerializer<Double>() {
    override fun serialize(value: Double, jgen: JsonGenerator, provider: SerializerProvider) {
        jgen.writeRawValue("%.4f".format(value))
    }
}

@JsonTypeName("power")
@JsonTypeInfo(include = JsonTypeInfo.As.WRAPPER_OBJECT, use = JsonTypeInfo.Id.NAME)
data class PowerCommand(
    @JsonSerialize(using = RoundSerializer::class) val left: Double,
    @JsonSerialize(using = RoundSerializer::class) val right: Double
) : IControlCommand
