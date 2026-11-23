"""Validate two-track MIDI exports. No audio renderer is included."""

def verify_midi(path,expected_counts):
    data = path.read_bytes()
    assert data[:4] == b"MThd" and int.from_bytes(data[10:12],"big") == 2
    position = 14
    counts = []
    def number(pos):
        value = 0
        while True:
            byte = data[pos]
            pos += 1
            value = (value << 7) | (byte & 127)
            if byte < 128:
                return value,pos
    for _ in range(2):
        assert data[position:position+4] == b"MTrk"
        length = int.from_bytes(data[position+4:position+8],"big")
        position += 8
        end = position+length
        count = 0
        while position < end:
            _,position = number(position)
            status = data[position]
            position += 1
            if status == 255:
                position += 1
                size,position = number(position)
                position += size
            elif status & 240 in (192,208):
                position += 1
            else:
                assert status & 240 in (128,144,160,176,224)
                if status & 240 == 144 and data[position+1] > 0:
                    count += 1
                position += 2
        assert position == end
        counts.append(count)
    assert counts == expected_counts
    return counts
