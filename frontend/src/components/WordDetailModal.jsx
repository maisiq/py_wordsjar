import { useEffect, useState } from 'react';
import { Modal, Spinner } from 'react-bootstrap';
import axiosService from '../api/axios';
import { describeError } from '../api/errors';

function WordDetailModal({ wordEn, show, onHide }) {
  const [loading, setLoading] = useState(false);
  const [word, setWord] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!show || !wordEn) {
      setWord(null);
      setError(null);
      return;
    }

    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setError(null);
      setWord(null);
      try {
        const { data } = await axiosService.get(
          `/words/${encodeURIComponent(wordEn)}`,
        );
        if (!cancelled) setWord(data);
      } catch (err) {
        if (!cancelled) {
          setError(
            describeError(err, 'Не удалось загрузить информацию о слове'),
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [show, wordEn]);

  const examples = word?.examples || [];

  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title>Детали слова</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {loading && (
          <div className="text-center">
            <Spinner animation="border" variant="primary" role="status">
              <span className="visually-hidden">Загрузка...</span>
            </Spinner>
          </div>
        )}
        {error && <div className="alert alert-danger">{error}</div>}
        {word && !loading && (
          <div className="word-detail">
            <h3 className="mb-3 text-primary">{word.en}</h3>
            <div className="mb-3">
              <strong>Транскрипция:</strong>
              <p className="fs-5 text-muted">[{word.transcription}]</p>
            </div>
            <div className="mb-3">
              <strong>Переводы:</strong>
              <ul className="list-group mt-2">
                {(word.ru || []).map((t, i) => (
                  <li key={i} className="list-group-item">
                    {i + 1}. {t}
                  </li>
                ))}
              </ul>
            </div>
            {examples.length > 0 && (
              <div className="mb-3">
                <strong>Примеры:</strong>
                <ul className="list-group mt-2">
                  {Array.from({ length: Math.ceil(examples.length / 2) }).map(
                    (_, i) => {
                      const en = examples[i * 2];
                      const ru = examples[i * 2 + 1];
                      return (
                        <li key={i} className="list-group-item">
                          {en}
                          <br />
                          <i>{ru}</i>
                        </li>
                      );
                    },
                  )}
                </ul>
              </div>
            )}
          </div>
        )}
      </Modal.Body>
    </Modal>
  );
}

export default WordDetailModal;
