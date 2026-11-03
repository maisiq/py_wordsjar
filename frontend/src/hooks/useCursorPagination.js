import { useCallback, useRef, useState } from 'react';

/**
 * Cursor-based pagination matching the vanilla app behaviour.
 * fetcher(params) should return { items, has_next, next_cursor }
 *
 * refresh() re-reads the CURRENT page with its stored cursor: after a word
 * is removed server-side the page is refilled from the following rows
 * instead of keeping a hole where the deleted item used to be.
 */
export function useCursorPagination(fetcher, { perPage = 30 } = {}) {
  const [items, setItems] = useState([]);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const cursorsRef = useRef({ 1: '' });
  // Номер последнего запроса: ответы устаревших запросов игнорируются,
  // чтобы быстрый переход между страницами/сортировками не перезаписывал список.
  const requestIdRef = useRef(0);

  const load = useCallback(
    async (direction = 'reset') => {
      setLoading(true);
      setError(null);

      let targetPage = page;
      let cursor = '';

      if (direction === 'reset') {
        targetPage = 1;
        cursorsRef.current = { 1: '' };
      } else if (direction === 'refresh') {
        // Та же страница тем же курсором: после удаления слова сервер
        // досылает в окно страницы следующие строки, и пустая клетка
        // на месте удалённой карточки не остаётся.
        cursor = cursorsRef.current[page] || '';
      } else if (direction === 'next') {
        targetPage = page + 1;
        cursor = cursorsRef.current[targetPage] || '';
        if (!cursor && hasNext) {
          setLoading(false);
          return load('reset');
        }
      } else if (direction === 'prev') {
        if (page <= 1) {
          setLoading(false);
          return;
        }
        targetPage = page - 1;
        cursor = cursorsRef.current[targetPage] || '';
        if (!cursor && targetPage > 1) {
          setLoading(false);
          return load('reset');
        }
      }

      const requestId = requestIdRef.current + 1;
      requestIdRef.current = requestId;

      try {
        const params = { per_page: perPage };
        if (cursor) params.cursor = cursor;

        const data = await fetcher(params);
        if (requestId !== requestIdRef.current) return;

        const list = data.items || [];

        if (list.length === 0 && targetPage > 1) {
          setHasNext(false);
          if (direction === 'refresh') {
            // На текущей странице больше нет слов (удалили последнее):
            // показываем предыдущую, чтобы не оставлять пустой экран.
            return load('prev');
          }
          setPage(Math.max(1, targetPage - 1));
          return;
        }

        setPage(targetPage);
        setHasNext(Boolean(data.has_next));
        if (data.has_next && data.next_cursor) {
          cursorsRef.current[targetPage + 1] = data.next_cursor;
        } else {
          delete cursorsRef.current[targetPage + 1];
        }

        setItems(list);
      } catch (err) {
        if (requestId !== requestIdRef.current) return;
        setError(err);
        setItems([]);
        setHasNext(false);
      } finally {
        if (requestId === requestIdRef.current) {
          setLoading(false);
        }
      }
    },
    [fetcher, page, hasNext, perPage],
  );

  const reset = useCallback(() => load('reset'), [load]);
  const refresh = useCallback(() => load('refresh'), [load]);
  const next = useCallback(() => load('next'), [load]);
  const prev = useCallback(() => load('prev'), [load]);

  return {
    items,
    setItems,
    page,
    hasNext,
    loading,
    error,
    load,
    reset,
    refresh,
    next,
    prev,
  };
}
