from dm_core.crypto.symmetric import SymmetricCrypto


class SecureMessage(object):

    def encrypt(self, key, data) -> dict:
        return self._encrypt(key, data)

    def decrypt(self, key, data) -> dict:
        return self._decrypt(key, data)

    def _decrypt(self, key, data):
        decrypter = SymmetricCrypto(key)
        for k, v in data.items():
            if type(v) == str:
                data[k] = decrypter.decrypt_data(v.encode()).decode()
            else:
                data[k] = self._decrypt(key, data[k])
        return data

    def _encrypt(self, key, data):
        encrypter = SymmetricCrypto(key)
        for k, v in data.items():
            if type(v) == str:
                data[k] = encrypter.encrypt_data(v.encode()).decode()
            else:
                data[k] = self._encrypt(key, data[k])
        return data