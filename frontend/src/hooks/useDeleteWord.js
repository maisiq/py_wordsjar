import { useCallback, useState } from 'react';
import toast from 'react-hot-toast';
import axiosService from '../api/axios';
import { describeError } from '../api/errors';

/**
 * Shared "remove word from jar" flow: confirm modal state + API call.
 * Used by both the words page and the jar page.
 *
 * onDeleted(en) is called after a successful delete so the page can update
 * its own list (toggle in_jar, drop the card, ...).
 */
export function useDeleteWord(onDeleted) {
  const [wordToDelete, setWordToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const requestDelete = useCallback((en) => {
    if (!en) return;
    setWordToDelete(en);
  }, []);

  const cancelDelete = useCallback(() => {
    setWordToDelete(null);
  }, []);

  const confirmDelete = useCallback(async () => {
    if (!wordToDelete || deleting) return;

    const en = wordToDelete;
    setDeleting(true);
    try {
      await axiosService.delete('/jar', { data: { word: en } });
      toast.success(`Слово «${en}» удалено из банки`);
      setWordToDelete(null);
      if (onDeleted) onDeleted(en);
    } catch (err) {
      toast.error(describeError(err, `Не удалось удалить слово «${en}»`));
    } finally {
      setDeleting(false);
    }
  }, [wordToDelete, deleting, onDeleted]);

  return {
    wordToDelete,
    deleting,
    requestDelete,
    cancelDelete,
    confirmDelete,
  };
}

export default useDeleteWord;