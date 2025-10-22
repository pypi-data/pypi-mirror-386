## Table of Contents

1. [String Functions](#string-functions)
2. [Math & Statistics](#math--statistics)
3. [List & Dict Operations](#list--dict-operations)
4. [File Operations](#file-operations)
5. [JSON Utilities](#json-utilities)
6. [HTTP Functions](#http-functions-new)
7. [System Functions](#system-functions)
8. [Type Conversion](#type-conversion)
9. [Iteration Functions](#iteration-functions)
10. [Utility Functions](#utility-functions)

---

## String Functions

### Basic String Operations

#### `panjang(string)` / `len(string)`
Mengembalikan panjang string.

```python
teks itu "Hello"
panjang_teks itu panjang(teks)  // 5
```

#### `huruf_besar(string)` / `upper(string)`
Mengubah string menjadi huruf besar.

```python
teks itu "hello"
besar itu huruf_besar(teks)  // "HELLO"
```

#### `huruf_kecil(string)` / `lower(string)`
Mengubah string menjadi huruf kecil.

```python
teks itu "HELLO"
kecil itu huruf_kecil(teks)  // "hello"
```

#### `huruf_kapital(string)` / `capitalize(string)`
Mengubah huruf pertama menjadi kapital.

```python
teks itu "hello world"
kapital itu huruf_kapital(teks)  // "Hello world"
```

#### `huruf_judul(string)` / `title(string)`
Mengubah setiap kata menjadi title case.

```python
teks itu "hello world"
judul itu huruf_judul(teks)  // "Hello World"
```

### String Manipulation

#### `potong(string, start, end)` / `slice(string, start, end)`
Memotong string dari index start sampai end.

```python
teks itu "Hello World"
bagian itu potong(teks, 0, 5)  // "Hello"
```

#### `ganti(string, old, new)` / `replace(string, old, new)`
Mengganti substring dengan string baru.

```python
teks itu "Hello World"
baru itu ganti(teks, "World", "Python")  // "Hello Python"
```

#### `pisah(string, separator)` / `split(string, separator)`
Memisahkan string menjadi list.

```python
teks itu "a,b,c,d"
list_hasil itu pisah(teks, ",")  // ["a", "b", "c", "d"]
```

#### `gabung(separator, list)` / `join(separator, list)`
Menggabungkan list menjadi string.

```python
items itu ["a", "b", "c"]
hasil itu gabung("-", items)  // "a-b-c"
```

#### `hapus_spasi(string)` / `strip(string)`
Menghapus spasi di awal dan akhir string.

```python
teks itu "  hello  "
bersih itu hapus_spasi(teks)  // "hello"
```

#### `hapus_spasi_kiri(string)` / `lstrip(string)`
Menghapus spasi di awal string.

```python
teks itu "  hello"
bersih itu hapus_spasi_kiri(teks)  // "hello"
```

#### `hapus_spasi_kanan(string)` / `rstrip(string)`
Menghapus spasi di akhir string.

```python
teks itu "hello  "
bersih itu hapus_spasi_kanan(teks)  // "hello"
```

### String Search & Validation

#### `cari(string, substring)` / `find(string, substring)`
Mencari posisi substring dalam string.

```python
teks itu "Hello World"
posisi itu cari(teks, "World")  // 6
```

#### `mulai_dengan(string, prefix)` / `startswith(string, prefix)`
Mengecek apakah string dimulai dengan prefix.

```python
teks itu "Hello World"
hasil itu mulai_dengan(teks, "Hello")  // benar
```

#### `akhiri_dengan(string, suffix)` / `endswith(string, suffix)`
Mengecek apakah string diakhiri dengan suffix.

```python
teks itu "Hello World"
hasil itu akhiri_dengan(teks, "World")  // benar
```

#### `adalah_angka(string)` / `isdigit(string)`
Mengecek apakah string hanya berisi angka.

```python
teks itu "12345"
hasil itu adalah_angka(teks)  // benar
```

#### `adalah_huruf(string)` / `isalpha(string)`
Mengecek apakah string hanya berisi huruf.

```python
teks itu "Hello"
hasil itu adalah_huruf(teks)  // benar
```

#### `adalah_alfanumerik(string)` / `isalnum(string)`
Mengecek apakah string hanya berisi huruf dan angka.

```python
teks itu "Hello123"
hasil itu adalah_alfanumerik(teks)  // benar
```

### String Formatting

#### `format_string(template, *args)` / `format(template, *args)`
Format string dengan placeholder.

```python
template itu "Nama: {}, Umur: {}"
hasil itu format_string(template, "Budi", 25)
// "Nama: Budi, Umur: 25"
```

#### `padding_kiri(string, width, char)` / `ljust(string, width, char)`
Menambahkan padding di kiri.

```python
teks itu "Hello"
hasil itu padding_kiri(teks, 10, " ")  // "Hello     "
```

#### `padding_kanan(string, width, char)` / `rjust(string, width, char)`
Menambahkan padding di kanan.

```python
teks itu "Hello"
hasil itu padding_kanan(teks, 10, " ")  // "     Hello"
```

#### `padding_tengah(string, width, char)` / `center(string, width, char)`
Menambahkan padding di tengah.

```python
teks itu "Hello"
hasil itu padding_tengah(teks, 10, " ")  // "  Hello   "
```

---

## Math & Statistics

### Basic Math

#### `abs(number)` / `absolut(number)`
Mengembalikan nilai absolut.

```python
nilai itu absolut(-5)  // 5
```

#### `round(number, digits)` / `bulat(number, digits)`
Membulatkan angka.

```python
nilai itu bulat(3.14159, 2)  // 3.14
```

#### `ceil(number)` / `pembulatan_atas(number)`
Membulatkan ke atas.

```python
nilai itu pembulatan_atas(3.2)  // 4
```

#### `floor(number)` / `pembulatan_bawah(number)`
Membulatkan ke bawah.

```python
nilai itu pembulatan_bawah(3.8)  // 3
```

#### `pow(base, exp)` / `pangkat(base, exp)`
Menghitung pangkat.

```python
nilai itu pangkat(2, 3)  // 8
```

#### `sqrt(number)` / `akar(number)`
Menghitung akar kuadrat.

```python
nilai itu akar(16)  // 4.0
```

### Trigonometry

#### `sin(angle)` / `sinus(angle)`
Menghitung sinus (dalam radian).

```python
nilai itu sinus(0)  // 0.0
```

#### `cos(angle)` / `cosinus(angle)`
Menghitung cosinus (dalam radian).

```python
nilai itu cosinus(0)  // 1.0
```

#### `tan(angle)` / `tangen(angle)`
Menghitung tangen (dalam radian).

```python
nilai itu tangen(0)  // 0.0
```

### Logarithms

#### `log(number, base)` / `logaritma(number, base)`
Menghitung logaritma.

```python
nilai itu logaritma(100, 10)  // 2.0
```

#### `ln(number)` / `logaritma_natural(number)`
Menghitung logaritma natural.

```python
nilai itu logaritma_natural(2.718)  // ~1.0
```

### Statistics

#### `mean(list)` / `rata_rata(list)`
Menghitung rata-rata.

```python
data itu [1, 2, 3, 4, 5]
rata itu rata_rata(data)  // 3.0
```

#### `median(list)` / `nilai_tengah(list)`
Menghitung median.

```python
data itu [1, 2, 3, 4, 5]
tengah itu nilai_tengah(data)  // 3
```

#### `mode(list)` / `modus(list)`
Menghitung modus.

```python
data itu [1, 2, 2, 3, 4]
mod itu modus(data)  // 2
```

#### `stdev(list)` / `deviasi_standar(list)`
Menghitung standar deviasi.

```python
data itu [1, 2, 3, 4, 5]
dev itu deviasi_standar(data)  // ~1.41
```

#### `variance(list)` / `variansi(list)`
Menghitung variansi.

```python
data itu [1, 2, 3, 4, 5]
var itu variansi(data)  // 2.0
```

### Random Numbers

#### `random()` / `acak()`
Menghasilkan angka acak 0-1.

```python
nilai itu acak()  // 0.xxx
```

#### `randint(min, max)` / `acak_bulat(min, max)`
Menghasilkan integer acak.

```python
nilai itu acak_bulat(1, 10)  // 1-10
```

#### `choice(list)` / `pilih_acak(list)`
Memilih elemen acak dari list.

```python
items itu ["a", "b", "c"]
pilihan itu pilih_acak(items)  // "a", "b", atau "c"
```

---

## List & Dict Operations

### List Operations

#### `tambah(list, item)` / `append(list, item)`
Menambahkan item ke list.

```python
data itu [1, 2, 3]
tambah(data, 4)  // [1, 2, 3, 4]
```

#### `hapus(list, item)` / `remove(list, item)`
Menghapus item dari list.

```python
data itu [1, 2, 3, 4]
hapus(data, 3)  // [1, 2, 4]
```

#### `masukkan(list, index, item)` / `insert(list, index, item)`
Menyisipkan item di index tertentu.

```python
data itu [1, 2, 4]
masukkan(data, 2, 3)  // [1, 2, 3, 4]
tampilkan data  // [1, 2, 3, 4]
```

#### `urutkan(list, terbalik=salah)`
Mengurutkan list secara in-place (mengubah list asli).

```python
data itu [3, 1, 4, 2]
urutkan(data)  // Mengubah data menjadi [1, 2, 3, 4]
tampilkan data  // [1, 2, 3, 4]

// Urutkan descending
data2 itu [3, 1, 4, 2]
urutkan(data2, terbalik=benar)
tampilkan data2  // [4, 3, 2, 1]
```

#### `sorted(list, reverse=salah)`
Mengembalikan list baru yang terurut (tidak mengubah list asli).

```python
data itu [3, 1, 4, 2]
hasil itu sorted(data)  // [1, 2, 3, 4]
tampilkan data   // [3, 1, 4, 2] - list asli tidak berubah
tampilkan hasil  // [1, 2, 3, 4]

// Sorted descending
hasil_desc itu sorted(data, reverse=benar)
tampilkan hasil_desc  // [4, 3, 2, 1]
```

#### `balikkan(list)`
Membalik urutan list secara in-place (mengubah list asli).

```python
data itu [1, 2, 3, 4]
balikkan(data)  // Mengubah data menjadi [4, 3, 2, 1]
tampilkan data  // [4, 3, 2, 1]
```

#### `terbalik(list)` / `reversed(list)`
Mengembalikan list baru dengan urutan terbalik (tidak mengubah list asli).

```python
data itu [1, 2, 3, 4]
hasil itu terbalik(data)  // [4, 3, 2, 1]
tampilkan data   // [1, 2, 3, 4] - list asli tidak berubah
tampilkan hasil  // [4, 3, 2, 1]
```

#### List Slicing (Pemotongan List)
Mengambil subset dari list menggunakan sintaks `[start:end:step]`.

**Sintaks:**
- `list[start:end]` - Elemen dari index start sampai end-1
- `list[:end]` - Elemen dari awal sampai end-1
- `list[start:]` - Elemen dari start sampai akhir
- `list[::step]` - Setiap step elemen
- `list[start:end:step]` - Kombinasi start, end, dan step
- `list[::-1]` - Reverse list
- `list[:]` - Copy list

**Contoh:**

```python
nums itu [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

// Basic slicing
tampilkan nums[2:5]      // [2, 3, 4]
tampilkan nums[1:8]      // [1, 2, 3, 4, 5, 6, 7]

// Dari awal
tampilkan nums[:5]       // [0, 1, 2, 3, 4]
tampilkan nums[:3]       // [0, 1, 2]

// Sampai akhir
tampilkan nums[5:]       // [5, 6, 7, 8, 9]
tampilkan nums[7:]       // [7, 8, 9]

// Dengan step
tampilkan nums[::2]      // [0, 2, 4, 6, 8] - setiap 2 elemen
tampilkan nums[1::2]     // [1, 3, 5, 7, 9] - mulai dari 1, setiap 2
tampilkan nums[::3]      // [0, 3, 6, 9] - setiap 3 elemen

// Kombinasi
tampilkan nums[1:8:2]    // [1, 3, 5, 7]
tampilkan nums[0:9:3]    // [0, 3, 6]

// Negative indices (dari belakang)
tampilkan nums[-3:]      // [7, 8, 9] - 3 terakhir
tampilkan nums[:-3]      // [0, 1, 2, 3, 4, 5, 6] - kecuali 3 terakhir
tampilkan nums[-5:-2]    // [5, 6, 7]

// Reverse
tampilkan nums[::-1]     // [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]

// Copy
copy itu nums[:]         // Salinan lengkap

// String slicing juga didukung
text itu "RenzmcLang"
tampilkan text[0:5]      // "Renzm"
tampilkan text[:6]       // "Renzmc"
tampilkan text[6:]       // "Lang"
tampilkan text[::-1]     // "gnaLcmzneR"
```

**Catatan:**
- Index end tidak termasuk dalam hasil
- Negative index menghitung dari belakang (-1 = elemen terakhir)
- Slicing tidak error jika index melebihi panjang list
- Step negatif membalik urutan

#### `jumlah(list)` / `sum(list)`
Menjumlahkan semua elemen.

```python
data itu [1, 2, 3, 4]
total itu jumlah(data)  // 10
```

#### `min(list)` / `nilai_minimum(list)`
Mencari nilai minimum.

```python
data itu [3, 1, 4, 2]
minimum itu min(data)  // 1
```

#### `max(list)` / `nilai_maksimum(list)`
Mencari nilai maksimum.

```python
data itu [3, 1, 4, 2]
maksimum itu max(data)  // 4
```

### Dict Operations

#### `kunci(dict)` / `keys(dict)`
Mendapatkan semua kunci.

```python
data itu {"a": 1, "b": 2}
keys itu kunci(data)  // ["a", "b"]
```

#### `nilai(dict)` / `values(dict)`
Mendapatkan semua nilai.

```python
data itu {"a": 1, "b": 2}
vals itu nilai(data)  // [1, 2]
```

#### `items(dict)` / `pasangan(dict)`
Mendapatkan pasangan key-value.

```python
data itu {"a": 1, "b": 2}
pairs itu items(data)  // [("a", 1), ("b", 2)]
```

#### `update(dict, other)` / `perbarui(dict, other)`
Memperbarui dictionary.

```python
data itu {"a": 1}
perbarui(data, {"b": 2})  // {"a": 1, "b": 2}
```

---

## File Operations

### File Reading

#### `baca_file(path)` / `read_file(path)`
Membaca seluruh file.

```python
content itu baca_file("data.txt")
```

#### `baca_baris(path)` / `read_lines(path)`
Membaca file per baris.

```python
lines itu baca_baris("data.txt")
```

### File Writing

#### `tulis_file(path, content)` / `write_file(path, content)`
Menulis ke file (overwrite).

```python
tulis_file("data.txt", "Hello World")
```

#### `tambah_file(path, content)` / `append_file(path, content)`
Menambahkan ke file.

```python
tambah_file("data.txt", "\nBaris baru")
```

### File Management

#### `ada_file(path)` / `file_exists(path)`
Mengecek apakah file ada.

```python
exists itu ada_file("data.txt")  // benar/salah
```

#### `hapus_file(path)` / `delete_file(path)`
Menghapus file.

```python
hapus_file("data.txt")
```

#### `salin_file(src, dst)` / `copy_file(src, dst)`
Menyalin file.

```python
salin_file("data.txt", "backup.txt")
```

#### `pindah_file(src, dst)` / `move_file(src, dst)`
Memindahkan file.

```python
pindah_file("data.txt", "folder/data.txt")
```

### Directory Operations

#### `buat_direktori(path)` / `create_directory(path)`
Membuat direktori.

```python
buat_direktori("folder_baru")
```

#### `hapus_direktori(path)` / `delete_directory(path)`
Menghapus direktori.

```python
hapus_direktori("folder_lama")
```

#### `daftar_file(path)` / `list_files(path)`
Mendaftar file dalam direktori.

```python
files itu daftar_file(".")
```

---

## JSON Utilities

#### `json_parse(string)` / `parse_json(string)`
Parse JSON string menjadi object.

```python
json_str itu '{"nama": "Budi", "umur": 25}'
data itu json_parse(json_str)
tampilkan data["nama"]  // "Budi"
```

#### `json_stringify(object)` / `to_json(object)`
Convert object menjadi JSON string.

```python
data itu {"nama": "Budi", "umur": 25}
json_str itu json_stringify(data)
// '{"nama": "Budi", "umur": 25}'
```

#### `json_baca(path)` / `read_json(path)`
Membaca file JSON.

```python
data itu json_baca("data.json")
```

#### `json_tulis(path, data)` / `write_json(path, data)`
Menulis ke file JSON.

```python
data itu {"nama": "Budi"}
json_tulis("data.json", data)
```

---

## HTTP Functions (NEW!)

### HTTP Requests

#### `http_get(url, params, headers, timeout)`
Melakukan HTTP GET request.

```python
response itu http_get("https://api.example.com/users")
tampilkan response.status_code  // 200

// With parameters
params itu {"page": 1, "limit": 10}
response itu http_get("https://api.example.com/users", params=params)

// With headers
headers itu {"Authorization": "Bearer token123"}
response itu http_get("https://api.example.com/data", headers=headers)

// With timeout
response itu http_get("https://api.example.com/data", timeout=10)
```

#### `http_post(url, data, json, headers, timeout)`
Melakukan HTTP POST request.

```python
// POST with JSON
data itu {"nama": "Budi", "email": "budi@example.com"}
response itu http_post("https://api.example.com/users", json=data)

// POST with form data
form_data itu {"username": "budi", "password": "secret"}
response itu http_post("https://api.example.com/login", data=form_data)
```

#### `http_put(url, data, json, headers, timeout)`
Melakukan HTTP PUT request.

```python
data itu {"nama": "Budi Updated"}
response itu http_put("https://api.example.com/users/1", json=data)
```

#### `http_delete(url, headers, timeout)`
Melakukan HTTP DELETE request.

```python
response itu http_delete("https://api.example.com/users/1")
```

#### `http_patch(url, data, json, headers, timeout)`
Melakukan HTTP PATCH request.

```python
data itu {"email": "newemail@example.com"}
response itu http_patch("https://api.example.com/users/1", json=data)
```

### HTTP Configuration

#### `http_set_header(key, value)`
Set default HTTP header.

```python
http_set_header("Authorization", "Bearer token123")
http_set_header("User-Agent", "MyApp/1.0")
```

#### `http_set_timeout(timeout)`
Set default HTTP timeout.

```python
http_set_timeout(30)  // 30 seconds
```

### Indonesian Aliases

#### `ambil_http(url, ...)`
Alias untuk `http_get`.

```python
response itu ambil_http("https://api.example.com/data")
```

#### `kirim_http(url, ...)`
Alias untuk `http_post`.

```python
data itu {"nama": "Budi"}
response itu kirim_http("https://api.example.com/users", json=data)
```

#### `perbarui_http(url, ...)`
Alias untuk `http_put`.

```python
data itu {"nama": "Budi Updated"}
response itu perbarui_http("https://api.example.com/users/1", json=data)
```

#### `hapus_http(url, ...)`
Alias untuk `http_delete`.

```python
response itu hapus_http("https://api.example.com/users/1")
```

### Response Object

HTTP response memiliki properties:

```python
response itu http_get("https://api.example.com/data")

// Properties
tampilkan response.status_code  // 200
tampilkan response.url          // URL
tampilkan response.text         // Response body
tampilkan response.headers      // Headers dict

// Methods
data itu response.json()        // Parse JSON
is_ok itu response.ok()         // Check if 200-299
```

---

## System Functions

#### `waktu_sekarang()` / `current_time()`
Mendapatkan waktu sekarang.

```python
waktu itu waktu_sekarang()
```

#### `tanggal_sekarang()` / `current_date()`
Mendapatkan tanggal sekarang.

```python
tanggal itu tanggal_sekarang()
```

#### `sleep(seconds)` / `tidur(seconds)`
Menunda eksekusi.

```python
tidur(2)  // Tidur 2 detik
```

#### `exit(code)` / `keluar(code)`
Keluar dari program.

```python
keluar(0)  // Exit dengan code 0
```

#### `env(key)` / `lingkungan(key)`
Mendapatkan environment variable.

```python
path itu env("PATH")
```

---

## Type Conversion

#### `ke_teks(value)` / `to_string(value)` / `str(value)`
Convert ke string.

```python
angka itu 123
teks itu ke_teks(angka)  // "123"
```

#### `ke_angka(value)` / `to_number(value)` / `float(value)`
Convert ke float.

```python
teks itu "3.14"
angka itu ke_angka(teks)  // 3.14
```

#### `ke_bulat(value)` / `to_integer(value)` / `int(value)`
Convert ke integer.

```python
teks itu "42"
bulat itu ke_bulat(teks)  // 42
```

#### `ke_boolean(value)` / `to_bool(value)` / `bool(value)`
Convert ke boolean.

```python
nilai itu ke_boolean(1)  // benar
```

#### `ke_list(value)` / `to_list(value)` / `list(value)`
Convert ke list.

```python
teks itu "hello"
chars itu ke_list(teks)  // ["h", "e", "l", "l", "o"]
```

---

## Iteration Functions

**PENTING:** `map`, `filter`, dan `reduce` adalah keywords di RenzmcLang. Gunakan alias Indonesia atau list comprehension sebagai alternatif.

#### `zip(list1, list2, ...)`
Menggabungkan beberapa list menjadi list of tuples.

```python
nama itu ["Alice", "Bob", "Charlie"]
umur itu [25, 30, 35]
kota itu ["Jakarta", "Bandung", "Surabaya"]

hasil itu zip(nama, umur, kota)
tampilkan hasil
// [("Alice", 25, "Jakarta"), ("Bob", 30, "Bandung"), ("Charlie", 35, "Surabaya")]
```

#### `enumerate(list)`
Menambahkan index ke setiap elemen list.

```python
items itu ["apel", "jeruk", "mangga"]
indexed itu enumerate(items)
tampilkan indexed
// [(0, "apel"), (1, "jeruk"), (2, "mangga")]

// Iterasi dengan enumerate
untuk setiap item dari indexed
    tampilkan f"Index {item[0]}: {item[1]}"
selesai
```

#### `range(start, stop, step)`
Menghasilkan sequence angka.

```python
// range(stop) - dari 0 sampai stop-1
untuk setiap i dari range(5)
    tampilkan i  // 0, 1, 2, 3, 4
selesai

// range(start, stop) - dari start sampai stop-1
untuk setiap i dari range(2, 8)
    tampilkan i  // 2, 3, 4, 5, 6, 7
selesai

// range(start, stop, step) - dengan step
untuk setiap i dari range(0, 10, 2)
    tampilkan i  // 0, 2, 4, 6, 8
selesai

// Membuat list dari range
angka itu list(range(5))
tampilkan angka  // [0, 1, 2, 3, 4]
```

#### List Comprehension (Alternatif untuk map/filter)
Gunakan list comprehension untuk transformasi dan filtering.

```python
// Map alternative - transformasi
angka itu [1, 2, 3, 4, 5]
kuadrat itu [x * x untuk setiap x dari angka]
tampilkan kuadrat  // [1, 4, 9, 16, 25]

// Filter alternative - filtering
genap itu [x untuk setiap x dari angka jika x % 2 == 0]
tampilkan genap  // [2, 4]

// Kombinasi transformasi dan filtering
genap_kuadrat itu [x * x untuk setiap x dari angka jika x % 2 == 0]
tampilkan genap_kuadrat  // [4, 16]

// Dengan range
kuadrat_10 itu [x * x untuk setiap x dari range(1, 11)]
tampilkan kuadrat_10  // [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]
```

---

## Utility Functions

#### `jenis(value)` / `type(value)`
Mendapatkan tipe data.

```python
nilai itu 123
tipe itu jenis(nilai)  // "int"
```

#### `id(value)` / `identitas(value)`
Mendapatkan ID object.

```python
obj itu [1, 2, 3]
obj_id itu id(obj)
```

#### `help(function)` / `bantuan(function)`
Mendapatkan bantuan fungsi.

```python
bantuan(panjang)
```

#### `dir(object)` / `daftar_atribut(object)`
Mendaftar atribut object.

```python
attrs itu dir([])
```

---

## Usage Examples

### Example 1: String Processing
```python
// Input
teks itu "  Hello World  "

// Process
bersih itu hapus_spasi(teks)
besar itu huruf_besar(bersih)
kata itu pisah(besar, " ")

// Output
tampilkan kata  // ["HELLO", "WORLD"]
```

### Example 2: Math Operations
```python
// Data
angka itu [1, 2, 3, 4, 5]

// Statistics
rata itu rata_rata(angka)
tengah itu nilai_tengah(angka)
dev itu deviasi_standar(angka)

// Output
tampilkan f"Rata-rata: {rata}"
tampilkan f"Median: {tengah}"
tampilkan f"Std Dev: {dev}"
```

### Example 3: HTTP Request
```python
// GET request
response itu http_get("https://jsonplaceholder.typicode.com/posts/1")

// Check status
jika response.ok()
    data itu response.json()
    tampilkan f"Title: {data['title']}"
    tampilkan f"Body: {data['body']}"
kalau_tidak
    tampilkan f"Error: {response.status_code}"
selesai
```

### Example 4: File Processing
```python
// Read file
content itu baca_file("data.txt")

// Process
lines itu pisah(content, "\n")
filtered itu filter(lambda dengan x -> panjang(x) > 0, lines)

// Write result
hasil itu gabung("\n", filtered)
tulis_file("output.txt", hasil)
```

---

## See Also

- [Syntax Basics](syntax-basics.md) - Basic syntax
- [Advanced Features](advanced-features.md) - Advanced features
- [Examples](examples.md) - Code examples
- [Python Integration](python-integration.md) - Python integratio