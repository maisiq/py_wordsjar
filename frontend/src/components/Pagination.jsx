function Pagination({ page, hasNext, onPrev, onNext, loading = false }) {
  if (page === 1 && !hasNext) {
    return null;
  }

  const prevDisabled = page <= 1 || loading;
  const nextDisabled = !hasNext || loading;

  return (
    <nav aria-label="Навигация по страницам" className="mt-3">
      <ul className="pagination justify-content-center">
        <li className={`page-item ${prevDisabled ? 'disabled' : ''}`}>
          <button
            type="button"
            className="page-link"
            aria-label="Предыдущая страница"
            disabled={prevDisabled}
            onClick={onPrev}
          >
            &lt;
          </button>
        </li>
        <li className="page-item active" aria-current="page">
          <span className="page-link">{page}</span>
        </li>
        <li className={`page-item ${nextDisabled ? 'disabled' : ''}`}>
          <button
            type="button"
            className="page-link"
            aria-label="Следующая страница"
            disabled={nextDisabled}
            onClick={onNext}
          >
            &gt;
          </button>
        </li>
      </ul>
    </nav>
  );
}

export default Pagination;