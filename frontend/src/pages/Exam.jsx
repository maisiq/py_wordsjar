import { useCallback, useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import axiosService from '../api/axios';
import { describeError } from '../api/errors';

// Транскрипции может не быть — тогда не показываем пустые скобки.
function formatWord(word) {
  return word.transcription ? `${word.en} [${word.transcription}]` : word.en;
}

function Exam() {
  const [words, setWords] = useState([]);
  const [index, setIndex] = useState(-1);
  const [answer, setAnswer] = useState('');
  const [result, setResult] = useState(null); // { ok, correctAnswer, examples }
  const [phase, setPhase] = useState('idle'); // idle | question | result | done
  const [loading, setLoading] = useState(true);

  const current = index >= 0 && index < words.length ? words[index] : null;

  const loadWords = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axiosService.get('/exam');
      const list = data?.items || [];
      setWords(list);
      setPhase('idle');
      setIndex(-1);
    } catch (err) {
      toast.error(describeError(err, 'Не удалось загрузить слова для теста'));
      setWords([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadWords();
  }, [loadWords]);

  const startTest = () => {
    if (words.length === 0) {
      toast.error('Нет слов для тестирования');
      return;
    }
    setIndex(0);
    setAnswer('');
    setResult(null);
    setPhase('question');
  };

  const showQuestion = useCallback(
    async (nextIndex) => {
      if (nextIndex >= words.length) {
        await loadWords();
        setIndex(-1);
        setPhase('idle');
        setResult(null);
        setAnswer('');
        return;
      }
      setIndex(nextIndex);
      setAnswer('');
      setResult(null);
      setPhase('question');
    },
    [words.length, loadWords],
  );

  const verify = async (e) => {
    e.preventDefault();
    if (!current) return;
    const value = answer.trim();
    if (!value) {
      toast.error('Введите ответ');
      return;
    }

    try {
      const { data } = await axiosService.post('/exam', {
        word_id: current.id,
        answer: value,
        reverse: current.reverse,
      });

      const correctAnswer = current.reverse
        ? formatWord(current)
        : (current.ru || []).join(', ');

      setResult({
        ok: Boolean(data.result),
        correctAnswer,
        examples: current.examples || [],
      });
      setPhase('result');
    } catch (err) {
      toast.error(describeError(err, 'Не удалось проверить ответ'));
    }
  };

  const nextQuestion = useCallback(() => {
    showQuestion(index + 1);
  }, [showQuestion, index]);

  // Enter на экране результата переводит к следующему вопросу.
  useEffect(() => {
    const onKey = (e) => {
      if (e.key !== 'Enter' || phase !== 'result') return;
      e.preventDefault();
      nextQuestion();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [phase, nextQuestion]);

  if (loading) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Загрузка...</span>
        </div>
      </div>
    );
  }

  const examples = result?.examples || [];

  return (
    <div>
      {words.length === 0 && phase === 'idle' && (
        <div className="card mb-4">
          <div className="card-body">
            <p className="text-center text-muted mb-0">
              В вашей банке нет слов для тестирования
            </p>
          </div>
        </div>
      )}

      {words.length > 0 && (
        <>
          <div className="card mb-4">
            <div className="card-header d-flex justify-content-between align-items-center">
              <h5 className="mb-0">Текущий вопрос</h5>
              <span className="badge bg-secondary">
                {phase === 'idle'
                  ? `0 / ${words.length}`
                  : `${index + 1} / ${words.length}`}
              </span>
            </div>
            <div className="card-body">
              {phase === 'idle' && (
                <div className="d-grid">
                  <button
                    type="button"
                    className="btn btn-success btn-lg"
                    onClick={startTest}
                  >
                    Начать тест
                  </button>
                </div>
              )}

              {(phase === 'question' || phase === 'result') && current && (
                <>
                  <div className="mb-3">
                    <h4 id="testWord" className="text-center mb-3">
                      {current.reverse
                        ? (current.ru || []).join(', ')
                        : formatWord(current)}
                    </h4>
                    <p id="testHint" className="text-muted text-center">
                      {current.reverse
                        ? 'Введите английское слово'
                        : 'Введите русский перевод'}
                    </p>
                  </div>

                  {phase === 'question' && (
                    <form onSubmit={verify}>
                      <div className="mb-3">
                        <label htmlFor="testAnswer" className="form-label">
                          Ваш ответ
                        </label>
                        <input
                          type="text"
                          className="form-control form-control-lg"
                          id="testAnswer"
                          required
                          autoFocus
                          autoComplete="off"
                          value={answer}
                          onChange={(e) => setAnswer(e.target.value)}
                        />
                      </div>
                      <button
                        type="submit"
                        className="btn btn-primary btn-lg w-100"
                      >
                        Проверить
                      </button>
                    </form>
                  )}
                </>
              )}
            </div>
          </div>

          {phase === 'result' && result && (
            <div
              className={`alert ${result.ok ? 'alert-success' : 'alert-danger'}`}
              role="alert"
            >
              {result.ok ? (
                <>
                  ✓ Правильно! <br />
                  <b>Дополнительно</b>: {result.correctAnswer}
                </>
              ) : (
                <>
                  ✗ Неправильно. <br />
                  <b>Правильный ответ:</b> {result.correctAnswer}
                </>
              )}
              {examples.length > 0 && (
                <>
                  <br />
                  <b>Примеры</b>:
                  <br />
                  <ul className="list-group mt-2">
                    {Array.from({
                      length: Math.ceil(examples.length / 2),
                    }).map((_, i) => (
                      <li key={i} className="list-group-item">
                        {examples[i * 2]}
                        <br />
                        <i>{examples[i * 2 + 1]}</i>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          )}

          {phase === 'result' && (
            <div className="d-grid gap-2">
              <button
                type="button"
                className="btn btn-primary btn-lg"
                onClick={nextQuestion}
              >
                Следующий вопрос
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default Exam;
