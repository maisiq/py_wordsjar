import { useState } from 'react';
import toast from 'react-hot-toast';
import axiosService from '../api/axios';
import { describeError } from '../api/errors';

function AddWordForm({ onAdded }) {
  const [en, setEn] = useState('');
  const [transcription, setTranscription] = useState('');
  const [ruText, setRuText] = useState('');
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const wordEn = en.trim();
    const tr = transcription.trim();
    const ru = ruText
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean);

    if (!wordEn || !tr || ru.length === 0) {
      toast.error('Заполните все поля');
      return;
    }

    setBusy(true);
    try {
      await axiosService.post('/words', {
        en: wordEn,
        transcription: tr,
        ru,
      });
      toast.success('Слово успешно добавлено!');
      setEn('');
      setTranscription('');
      setRuText('');
      if (onAdded) onAdded();
    } catch (err) {
      toast.error(describeError(err, 'Не удалось добавить слово'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card mb-4">
      <div className="card-header">
        <h5 className="mb-0">Добавить новое слово</h5>
      </div>
      <div className="card-body">
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label htmlFor="wordEN" className="form-label">
              Английское слово *
            </label>
            <input
              type="text"
              className="form-control"
              id="wordEN"
              required
              value={en}
              onChange={(e) => setEn(e.target.value)}
            />
          </div>
          <div className="mb-3">
            <label htmlFor="wordTranscription" className="form-label">
              Транскрипция *
            </label>
            <input
              type="text"
              className="form-control"
              id="wordTranscription"
              required
              value={transcription}
              onChange={(e) => setTranscription(e.target.value)}
            />
          </div>
          <div className="mb-3">
            <label htmlFor="wordRU" className="form-label">
              Русские переводы (каждый с новой строки) *
            </label>
            <textarea
              className="form-control"
              id="wordRU"
              rows={3}
              required
              value={ruText}
              onChange={(e) => setRuText(e.target.value)}
            />
            <small className="form-text text-muted">
              Введите переводы, разделяя их переносами строки
            </small>
          </div>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            Добавить слово
          </button>
        </form>
      </div>
    </div>
  );
}

export default AddWordForm;
