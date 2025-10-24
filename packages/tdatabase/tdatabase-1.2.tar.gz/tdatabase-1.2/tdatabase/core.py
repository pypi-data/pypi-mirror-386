import struct
import os
import hashlib

MAGIC = b'PXDB'

class TDatabase:
    def __init__(self):
        self.filename = None
        self.categories = {}
        self.rows = 0

    def open(self, filename):
        self.filename = filename
        if not os.path.exists(filename):
            self._create_file()
        self._load()

    def _create_file(self):
        with open(self.filename, 'wb') as f:
            f.write(MAGIC)
            f.write(struct.pack('<I', 0))

    def _load(self):
        self.categories = {}
        with open(self.filename, 'rb') as f:
            if f.read(4) != MAGIC:
                raise Exception("Invalid file format")
            self.rows, = struct.unpack('<I', f.read(4))
            for _ in range(self.rows):
                row_id, = struct.unpack('<I', f.read(4))
                cat_len, = struct.unpack('<H', f.read(2))
                category = f.read(cat_len).decode('utf-8')
                data_type = f.read(1).decode('utf-8')
                data_len, = struct.unpack('<H', f.read(2))
                data_bytes = f.read(data_len)
                data = self._deserialize_data(data_bytes, data_type)
                if category not in self.categories:
                    self.categories[category] = []
                self.categories[category].append((row_id, data))

    def _serialize_data(self, data):
        if isinstance(data, int):
            return b'i', struct.pack('<i', data)
        elif isinstance(data, float):
            return b'f', struct.pack('<f', data)
        else:
            encoded = str(data).encode('utf-8')
            return b's', encoded

    def _deserialize_data(self, data_bytes, data_type):
        if data_type == 'i':
            return struct.unpack('<i', data_bytes)[0]
        elif data_type == 'f':
            return struct.unpack('<f', data_bytes)[0]
        else:
            return data_bytes.decode('utf-8')

    def append_category(self, category_name):
        if category_name not in self.categories:
            self.categories[category_name] = []

    def append_cell(self, data, category, password=False):
        if category not in self.categories:
            self.append_category(category)
        if password and isinstance(data, str):
            data = hashlib.sha256(data.encode('utf-8')).hexdigest()
        row_id = self.rows + 1
        self.categories[category].append((row_id, data))
        self._save_cell(row_id, category, data)
        self.rows += 1
        self._update_row_count()

    def _save_cell(self, row_id, category, data):
        cat_bytes = category.encode('utf-8')
        data_type, data_bytes = self._serialize_data(data)
        with open(self.filename, 'ab') as f:
            f.write(struct.pack('<I', row_id))
            f.write(struct.pack('<H', len(cat_bytes)))
            f.write(cat_bytes)
            f.write(data_type)
            f.write(struct.pack('<H', len(data_bytes)))
            f.write(data_bytes)

    def _update_row_count(self):
        with open(self.filename, 'r+b') as f:
            f.seek(4)
            f.write(struct.pack('<I', self.rows))

    def search(self, category, keyword):
        if category not in self.categories:
            return []
        results = []
        for row_id, data in self.categories[category]:
            if isinstance(data, str) and keyword.lower() in data.lower():
                results.append((row_id, data))
            elif str(keyword) == str(data):
                results.append((row_id, data))
        return results

    def delete_row(self, category, row_id):
        if category not in self.categories:
            return False
        original = len(self.categories[category])
        self.categories[category] = [(r, d) for r, d in self.categories[category] if r != row_id]
        if len(self.categories[category]) < original:
            self._rewrite_file()
            return True
        return False

    def update_cell(self, category, row_id, new_data):
        if category not in self.categories:
            return False
        updated = False
        for i, (r, d) in enumerate(self.categories[category]):
            if r == row_id:
                self.categories[category][i] = (r, new_data)
                updated = True
                break
        if updated:
            self._rewrite_file()
        return updated

    def _rewrite_file(self):
        with open(self.filename, 'wb') as f:
            f.write(MAGIC)
            f.write(struct.pack('<I', 0))
        self.rows = 0
        for category in self.categories:
            for row_id, data in self.categories[category]:
                self._save_cell(row_id, category, data)
                self.rows += 1
        self._update_row_count()

    def select_all(self, category=None):
        if category:
            return self.categories.get(category, [])
        return self.categories
