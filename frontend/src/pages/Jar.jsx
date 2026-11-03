import { useCallback, useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import axiosService from '../api/axios';
import { describeError } from '../api/errors';
import { useCursorPagination } from '../hooks/useCursorPagination';
import { useDeleteWord } from '../hooks/useDeleteWord';
import WordCard from '../components/WordCard';
import Pagination from '../components/Pagination';
import SortDropdown from '../components/SortDropdown';
import WordDetailModal from '../components/WordDetailModal';
import AddToJarModal from '../components/AddToJarModal';
import DeleteWordModal from '../components/DeleteWordModal';

/**
 * Варианты сортировки банки: подпись -> параметры запроса /jar.
 * Бэкенд принимает order_by (поля через запятую) и desc.
 */
const SORT_OPTIONS = [
  {
    key: 'know_better',
    label: 'Знаю лучше',
    orderBy: 'rating,id',
    desc: true,
  },
  {
    key: 'know_worse',
    label: 'Знаю хуже',
    orderBy: 'rating,id',
    desc: false,
  },
  {
    key: 'alphabet',
    label: 'По алфавиту',
    orderBy: 'en,id',
    desc: false,
  },
];

// Совпадает с сортировкой по умолчанию на бэкенде (rating, id по возрастанию).
const DEFAULT_SORT_KEY = 'know_worse';

function Jar() {
  const [detailWord, setDetailWord] = useState(null);
  const [showAdd, setShowAdd] = useState(false);
  const [sortKey, setSortKey] = useState(DEFAULT_SORT_KEY);

  const fetcher = useCallback(
    async (params) => {
      const option =
        SORT_OPTIONS.find((item) => item.key === sortKey) || SORT_OPTIONS[0];
      const { data } = await axiosService.get('/jar', {
        params: {
          ...params,
          order_by: option.orderBy,
          desc: option.desc,
        },
      });
      return data;
    },
    [sortKey],
  );

  const { items, page, hasNext, loading, error, reset, refresh, next, prev } =
    useCursorPagination(fetcher);

  const handleSortChange = useCallback((key) => {
    setSortKey((prev) => (prev === key ? prev : key));
  }, []);

  useEffect(() => {
    reset();
  }, [sortKey]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (error) {
      toast.error(describeError(error, 'Не удалось загрузить слова из банки'));
    }
  }, [error]);

  const handleDeleted = useCallback(() => {
    // Слово уже удалено на сервере. Перечитываем текущую страницу, а не
    // вырезаем карточку локально: страница добирает слова со следующих
    // позиций и в сетке не остаётся пустого места на месте удалённого
    // слова (а опустевшая страница сама сменяется предыдущей).
    refresh();
  }, [refresh]);

  const {
    wordToDelete,
    deleting,
    requestDelete,
    cancelDelete,
    confirmDelete,
  } = useDeleteWord(handleDeleted);

  return (
    <>
      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <button
            className="btn btn-sm btn-outline-primary"
            type="button"
            onClick={() => setShowAdd(true)}
          >
            Добавить слова
          </button>

          <SortDropdown
            options={SORT_OPTIONS}
            value={sortKey}
            onChange={handleSortChange}
          />
        </div>
        <div className="card-body">
          <div className="words-row">
            {loading && (
              <div className="words-row-message">
                <div className="spinner-border text-primary" role="status">
                  <span className="visually-hidden">Загрузка...</span>
                </div>
              </div>
            )}
            {!loading && items.length === 0 && (
              <div className="words-row-message text-muted">
                В вашей банке пока нет слов
              </div>
            )}
            {!loading &&
              items.map((word) => (
                <WordCard
                  key={word.en + (word.id || '')}
                  word={word}
                  inJar
                  onOpen={setDetailWord}
                  onDelete={requestDelete}
                  actionDisabled={deleting}
                />
              ))}
          </div>

          <Pagination
            page={page}
            hasNext={hasNext}
            loading={loading}
            onPrev={prev}
            onNext={next}
          />
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

      <AddToJarModal
        show={showAdd}
        onHide={() => setShowAdd(false)}
        onAdded={() => reset()}
      />
    </>
  );
}

export default Jar;
