import { useState } from 'react';
import { Modal } from 'react-bootstrap';
import toast from 'react-hot-toast';
import axiosService from '../api/axios';
import { describeError } from '../api/errors';

function wordsLabel(count) {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return 'слово';
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return 'слова';
  return 'слов';
}

function AddToJarModal({ show, onHide, onAdded }) {
  const [level, setLevel] = useState('new');
  const [words, setWords] = useState('');
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const wordList = words
      .replace(/\r\n/g, '\n')
      .split('\n')
      .map((word) => word.trim())
      .filter(Boolean);

    if (wordList.length === 0) {
      toast.error('Введите хотя бы одно английское слово');
      return;
    }

    setBusy(true);
    try {
      const { data } = await axiosService.post('/jar', {
        words_en: wordList,
        status: level,
      });
      const added = Number(data?.count) || 0;
      if (added === 0) {
        toast('Эти слова уже есть в банке', { icon: 'ℹ️' });
      } else {
        toast.success(`Добавлено ${added} ${wordsLabel(added)}`);
      }
      setWords('');
      setLevel('new');
      onHide();
      if (onAdded) onAdded();
    } catch (err) {
      toast.error(describeError(err, 'Не удалось добавить слова в банку'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title>Добавить слова в банку</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label htmlFor="word-level" className="form-label">
              Как хорошо вы знаете слова:
            </label>
            <select
              className="form-select"
              id="word-level"
              value={level}
              onChange={(e) => setLevel(e.target.value)}
            >
              <option value="new">Новые для меня</option>
              <option value="wellknown">Отлично</option>
              <option value="medium">Хорошо</option>
            </select>

            <label htmlFor="jarWordEN" className="form-label mt-3">
              Английские слова *
            </label>
            <textarea
              className="form-control"
              id="jarWordEN"
              rows={4}
              placeholder="Каждое слово с новой строки"
              required
              value={words}
              onChange={(e) => setWords(e.target.value)}
            />
            <small className="form-text text-muted">
              Можно добавить сразу несколько слов — введите каждое слово с новой
              строки
            </small>
          </div>
          <button
            type="submit"
            className="btn btn-primary w-100"
            disabled={busy}
          >
            Добавить в банку
          </button>
        </form>
      </Modal.Body>
    </Modal>
  );
}

export default AddToJarModal;