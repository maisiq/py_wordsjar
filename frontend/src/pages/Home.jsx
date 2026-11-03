import { useCallback, useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import axiosService from '../api/axios';
import { describeError } from '../api/errors';
import { useAuth } from '../context/AuthContext';
import { useCursorPagination } from '../hooks/useCursorPagination';
import { useDeleteWord } from '../hooks/useDeleteWord';
import SearchBar from '../components/SearchBar';
import WordCard from '../components/WordCard';
import Pagination from '../components/Pagination';
import WordDetailModal from '../components/WordDetailModal';
import AddWordForm from '../components/AddWordForm';
import DeleteWordModal from '../components/DeleteWordModal';

function Home() {
  const { isAuthenticated, isAdmin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();

  // Поиск живёт в URL (?q=...): ссылкой можно поделиться, F5 не сбрасывает.
  const urlQuery = (searchParams.get('q') || '').trim();
  const searchMode = urlQuery.length > 0;

  const [detailWord, setDetailWord] = useState(null);
  const [searchQuery, setSearchQuery] = useState(urlQuery);
  const [searchItems, setSearchItems] = useState([]);
  const [searchLoading, setSearchLoading] = useState(searchMode);
  // Номер последнего поискового запроса: ответы устаревших игнорируются.
  const searchRequestRef = useRef(0);

  const fetcher = useCallback(async (params) => {
    const { data } = await axiosService.get('/words', { params });
    return data;
  }, []);

  const {
    items,
    setItems,
    page,
    hasNext,
    loading,
    error,
    reset,
    next,
    prev,
  } = useCursorPagination(fetcher);

  // Поле ввода следует за URL: работают «назад», сброс и прямые ссылки.
  useEffect(() => {
    setSearchQuery(urlQuery);
  }, [urlQuery]);

  // Выход из режима поиска возвращает список слов на первую страницу.
  useEffect(() => {
    if (!searchMode) reset();
  }, [searchMode]); // eslint-disable-line react-hooks/exhaustive-deps

  // Пункт «СЛОВА» в меню: сбрасываем и поиск, и пагинацию.
  useEffect(() => {
    if (!location.state?.resetWords) return;

    setSearchParams({}, { replace: true });
    reset();
    navigate('/', { replace: true, state: null });
  }, [location.state, navigate, reset, setSearchParams]);

  useEffect(() => {
    if (error) {
      toast.error(describeError(error, 'Не удалось загрузить слова'));
    }
  }, [error]);

  // Запрос уходит при каждом изменении ?q=.
  useEffect(() => {
    if (!urlQuery) return undefined;

    const requestId = searchRequestRef.current + 1;
    searchRequestRef.current = requestId;
    setSearchLoading(true);

    const run = async () => {
      try {
        const { data } = await axiosService.get('/search', {
          params: { query: urlQuery },
        });
        if (requestId !== searchRequestRef.current) return;
        // API может вернуть { items }, список или одно слово
        const list = Array.isArray(data)
          ? data
          : data.items || (data.en ? [data] : []);
        setSearchItems(list);
        if (list.length === 0) {
          toast('Слова не найдены', { icon: 'ℹ️' });
        }
      } catch (err) {
        if (requestId !== searchRequestRef.current) return;
        // fallback: пробуем точное совпадение по слову
        try {
          const { data } = await axiosService.get(
            `/words/${encodeURIComponent(urlQuery)}`,
          );
          if (requestId !== searchRequestRef.current) return;
          setSearchItems(data?.en ? [data] : []);
        } catch {
          if (requestId !== searchRequestRef.current) return;
          toast.error(describeError(err, 'Не удалось выполнить поиск'));
          setSearchItems([]);
        }
      } finally {
        if (requestId === searchRequestRef.current) {
          setSearchLoading(false);
        }
      }
    };

    run();
    return undefined;
  }, [urlQuery]);

  const handleSearch = (query) => {
    const q = query.trim();
    setSearchParams(q ? { q } : {}, { replace: true });
  };

  const handleAddToJar = async (wordEn) => {
    if (!isAuthenticated) {
      // Кнопка «+» видна и гостям: отправляем их входить, вернув на эту страницу.
      toast('Войдите, чтобы добавлять слова в банку', { icon: 'i️' });
      navigate('/login', { state: { from: location } });
      return;
    }
    try {
      await axiosService.post('/jar', { words_en: [wordEn] });
      toast.success('Слово добавлено в банку!');
      const mark = (list) =>
        list.map((w) => (w.en === wordEn ? { ...w, in_jar: true } : w));
      if (searchMode) {
        setSearchItems((prev) => mark(prev));
      } else {
        setItems((prev) => mark(prev));
      }
    } catch (err) {
      toast.error(describeError(err, 'Не удалось добавить слово в банку'));
    }
  };

  const displayItems = searchMode ? searchItems : items;
  const isLoading = searchMode ? searchLoading : loading;

  const handleDeleted = useCallback(
    (en) => {
      const mark = (list) =>
        list.map((w) => (w.en === en ? { ...w, in_jar: false } : w));
      setItems(mark);
      setSearchItems(mark);
    },
    [setItems],
  );

  const {
    wordToDelete,
    deleting,
    requestDelete,
    cancelDelete,
    confirmDelete,
  } = useDeleteWord(handleDeleted);

  return (
    <>
      <SearchBar
        query={searchQuery}
        onQueryChange={setSearchQuery}
        onSearch={handleSearch}
      />

      {isAdmin && <AddWordForm onAdded={() => reset()} />}

      <div className="card">
        <div className="card-body">
          <div className="words-row">
            {isLoading && (
              <div className="words-row-message">
                <div className="spinner-border text-primary" role="status">
                  <span className="visually-hidden">Загрузка...</span>
                </div>
              </div>
            )}
            {!isLoading && displayItems.length === 0 && (
              <div className="words-row-message text-muted">
                Слова не найдены
              </div>
            )}
            {!isLoading &&
              displayItems.map((word) => {
                // У гостя банки нет: in_jar мог приехать из залогиненной
                // сессии (список не перечитывается при выходе), и тогда
                // карточка осталась бы совсем без кнопок: «+» не положен
                // (слово «в банке»), «x» не кому удалять.
                const cardWord = isAuthenticated
                  ? word
                  : { ...word, in_jar: false };
                return (
                  <WordCard
                    key={word.en + (word.id || '')}
                    word={cardWord}
                    onAddToJar={handleAddToJar}
                    onDelete={isAuthenticated ? requestDelete : undefined}
                    onOpen={setDetailWord}
                  />
                );
              })}
          </div>

          {!searchMode && (
            <Pagination
              page={page}
              hasNext={hasNext}
              loading={loading}
              onPrev={prev}
              onNext={next}
            />
          )}
        </div>
      </div>

      <WordDetailModal
        wordEn={detailWord}
        show={Boolean(detailWord)}
        onHide={() => setDetailWord(null)}
      />

      <DeleteWordModal
        word={wordToDelete}
        busy={deleting}
        onHide={cancelDelete}
        onConfirm={confirmDelete}
      />
    </>
  );
}

export default Home;