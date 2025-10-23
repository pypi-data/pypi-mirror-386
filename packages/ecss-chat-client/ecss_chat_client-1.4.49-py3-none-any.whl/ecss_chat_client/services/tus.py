from typing import Optional

from requests import Response

from .lib import Base


class TusService(Base):
    """Сервис для работы с файл сервисом."""

    @staticmethod
    def __init_tus_init_header(
            file_size: str | int,
            file_name: str,
            file_type: str,
    ) -> dict:
        """Создание header для инициализации загрузки по TUS.

        :param file_size: Размер файла
        :param file_name: Название файла
        :param file_type: MIME тип файла

        :return: dict
        """
        tus_header = {
            'Upload-Length': str(file_size),
            'Upload-Metadata': f'filename {file_name},'
                               f'filetype {file_type}',
            'Tus-Resumable': '1.0.0',
            'Content-Length': '0',
        }
        return tus_header

    @staticmethod
    def __init_tus_chunk_upload_header(
            chunk_size: str,
            upload_offset: str,
    ) -> dict:
        """Создание header для продолжения загрузки по TUS.

        :param chunk_size: Чанк для загрузки
        :param upload_offset: Смещение загрузки

        :return: dict
        """
        chunk_header = {
            'Content-Type': 'application/offset+octet-stream',
            'Upload-Offset': upload_offset,
            'Content-Length': chunk_size,
            'Tus-Resumable': '1.0.0',
        }
        return chunk_header

    def init_upload(
            self,
            file_size: int,
            file_name: str,
            file_type: str,
    ) -> Response:
        """Инициализация загрузки по TUS.

        :param file_size: Размер файла
        :param file_name: Название файла
        :param file_type: MIME тип файла

        :return: Request
        """
        init_header = self.__init_tus_init_header(
            file_size=file_size,
            file_name=file_name,
            file_type=file_type,
        )
        self.client.session.headers.update(init_header)
        return self._make_request(
            endpoint='elph/store/tus',
            method='POST',
            tus_path=True,
        )

    def init_upload_many_files(self, data: list[dict]) -> Response:
        """Инициализация загрузки множества файлов по TUS.

        :param data: информация о файлах

        :return: Request
        """
        return self._make_request(
            endpoint='elph/store/files/batch',
            method='POST',
            tus_path=True,
            payload=data,
        )

    def upload_chunk(
            self,
            chunk: bytes,
            file_id: str,
            upload_offset: Optional[int] = 0,
    ) -> Response:
        """Загрузка чанка по TUS.

        :param chunk: Чанк
        :param file_id: id файла
        :param upload_offset: смещение загрузки

        :return: Request
        """
        upload_header = self.__init_tus_chunk_upload_header(
            chunk_size=str(chunk),
            upload_offset=str(upload_offset),
        )
        self.client.session.headers.update(upload_header)
        return self._make_request(
            endpoint=f'elph/store/tus/{file_id}',
            payload=chunk,
            method='PATCH',
            tus_path=True,
        )

    def full_upload(
            self,
            file_id: str,
            file_path: str,
            chunk_size: int,
    ) -> None:
        """Полная загрузка файла по TUS.

        :param file_id: uid файла
        :param file_path: путь до файла
        :param chunk_size: размер чанка

        :return: None
        """
        with open(file_path, 'rb') as file:
            while True:
                status_request = self.get_upload_status(
                    file_id=file_id,
                )
                status_offset = status_request.headers.get('Upload-Offset')
                status_upload_len = status_request.headers.get('Upload-Length')
                if status_offset == status_upload_len:
                    break
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                request = self.upload_chunk(
                    chunk=chunk,
                    file_id=file_id,
                    upload_offset=status_offset,
                )
                if request.status_code != 204:
                    raise Exception(f'Tus upload exception: {request.text}')

    def full_upload_with_offset(
            self,
            file_id: str,
            file_path: str,
            chunk_size: int,
            file_size: int,
            offset: int,
    ) -> None:
        """Полная загрузка файла по TUS с указанием upload-offset.

        :param file_id: uid файла
        :param file_path: путь до файла
        :param chunk_size: размер чанка
        :param file_size: размер файла
        :param offset: смещение загрузки

        :return: None
        """
        with open(file_path, 'rb') as file:
            file.seek(offset)
            while offset < file_size:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                request = self.upload_chunk(
                    chunk=chunk,
                    file_id=file_id,
                    upload_offset=offset,
                )
                if request.status_code == 204:
                    offset = int(request.headers['Upload-Offset'])
                else:
                    raise Exception(f'Tus upload exception: {request.text}')

    def get_upload_status(self, file_id: str) -> Response:
        """Получение статуса загрузки файла по TUS.

        :param file_id: id файла

        :return: Request
        """
        self.client.session.headers.update(
            {
                'Tus-Resumable': '1.0.0',
            },
        )
        return self._make_request(
            endpoint=f'elph/store/tus/{file_id}',
            method='HEAD',
            tus_path=True,
        )
