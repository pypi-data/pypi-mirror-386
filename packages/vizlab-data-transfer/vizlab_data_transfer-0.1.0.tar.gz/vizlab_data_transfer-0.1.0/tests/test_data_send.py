import socket
from vizlab_data_transfer import vizlab
import pytest
import numpy as np
from pytest_mock import MockerFixture


class TestDataSendMethods:

    def test_compatible_object_types(self, mocker: MockerFixture):
        # Cache current socket state (to be reset later)
        currentIP = vizlab.get_ip()
        currentPort = vizlab.get_port()

        # Init socket state for test
        vizlab._reset_socket_state()
        vizlab.set_ip("127.0.0.1")
        vizlab.set_port(26000)

        # Mock the socket.socket constructor
        mock_socket_instance = mocker.MagicMock()
        mocker.patch("socket.socket", return_value=mock_socket_instance)

        # Set recv return values using mocker side effects
        mock_socket_instance.recv.side_effect = [
            (8).to_bytes(4, byteorder="little"),
            b"RESPONSE",
        ]

        # Assertions
        assert vizlab.send([np.random.rand(10, 2)]) == "RESPONSE"
        mock_socket_instance.connect.assert_called_with(("127.0.0.1", 26000))

        with pytest.raises(
            ValueError,
            match="Provided Python objects must be one of the following types: numpy ndarray or recarray, pandas dataframe, astropy FITS table, matplotlib figure, PIL image.",
        ):
            vizlab.send(21912912)

        # Bring socket state back to what it was pre-test
        vizlab._reset_socket_state()
        try:
            vizlab.set_ip(currentIP)
        except:
            print("did not reset ip as it was invalid")
        else:
            print("reset ip")
        try:
            vizlab.set_port(currentPort)
        except:
            print("did not reset port as it was invalid")
        else:
            print("reset port")
