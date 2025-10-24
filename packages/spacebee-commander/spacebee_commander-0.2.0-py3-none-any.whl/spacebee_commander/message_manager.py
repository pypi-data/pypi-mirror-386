import struct

from spacebee_commander.telecommand_interface import TelecommandInterface


class MessageManager:

    __header_format='<QHBQHHHBH'
    __last_transaction_id=0

    def make_header(self, telecommand: TelecommandInterface, type):
        timestamp=0
        MessageManager.__last_transaction_id += 1

        return struct.pack(self.__header_format, timestamp,
                                type,
                                telecommand.interaction_stage,
                                MessageManager.__last_transaction_id,
                                telecommand.service,
                                telecommand.operation,
                                telecommand.area_version,
                                telecommand.is_error_message,
                                telecommand.body_length)

    def make_CRC(self, header, body):
        "Make CRC with 16 bits CTC-16-CCITT with polynomial x^16+x^12+x^5+1."
        data=header+body
        crc = 0xFFFF
        for byte in data:
            crc ^= (byte << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1

        return crc & 0xFFFF

    def check_CRC(self,header,body,crc_check):
        crc=self.make_CRC(header,body).to_bytes(2, 'little')
        if crc == crc_check:
            return True
        else:
            return False

    def make_message(self,telecommand, type):
        header= self.make_header(telecommand,type)
        crc=self.make_CRC(header,telecommand.body).to_bytes(2, 'little')
        # print(f"Header:{header} + body:{telecommand.body} + crc: {crc}")
        return header+telecommand.body+crc

    def unpack(self,response):
        header_size = struct.calcsize(self.__header_format)
        header_data = response[:header_size]
        timestamp, interaction_type, interaction_stage, transaction_id, service, operation, area_version, is_error_message, body_length = struct.unpack(self.__header_format, header_data)
        body_response = response[header_size:-2]
        crc_response = response[-2:]

        if interaction_stage!=1:   #Checkea que el interaction type es una respuesta del mensaje
            if not is_error_message:

                if self.check_CRC(header_data,body_response,crc_response):

                    if interaction_type==2:
                        print(f"body:{body_response}")
                        if not body_response:
                            return True
                        else:
                            return False          #ACK is empty body

                    elif interaction_type==3:
                        #Search for a telecommand with operation and execute the function parseOutputArguments
                        return body_response

                    elif interaction_type==6:
                        #It is telemetry
                        print("Error is telemetry")

                else:
                    print("CRC check failed. Error in the communication detected.")
            else:
                print("The message is an error")
        else:
            print("Error, interaction stage not valid")
