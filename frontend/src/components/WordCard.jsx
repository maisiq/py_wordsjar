function PlusIcon() {
  return (
    <svg className="word-card-add-icon" viewBox="0 0 16 16" aria-hidden="true">
      <path
        d="M8 3.5v9M3.5 8h9"
        fill="none"
        stroke="currentColor"
        strokeWidth="3.0"
        strokeLinecap="round"
      />
    </svg>
  );
}

function DeleteIcon() {
  return (
    <img
      className="word-card-delete-icon"
      src="/delete-word-x.png"
      alt=""
      aria-hidden="true"
    />
  );
}

/**
 * Word card with a single contextual action:
 * plus  - add to jar (word is not in the jar, onAddToJar provided);
 * cross - remove from jar (word is in the jar, onDelete provided).
 *
 * `inJar` can be passed explicitly for pages where every word belongs to the
 * jar (jar page); otherwise `word.in_jar` is used.
 */
function WordCard({
  word,
  inJar: inJarProp,
  onOpen,
  onAddToJar,
  onDelete,
  actionDisabled = false,
}) {
  const inJar = inJarProp ?? Boolean(word.in_jar);
  const en = word.en;

  const canAdd = !inJar && Boolean(onAddToJar);
  const canDelete = inJar && Boolean(onDelete);
  const showAction = canAdd || canDelete;

  const runAction = (e, handler) => {
    e.stopPropagation();
    if (actionDisabled || !handler) return;
    handler(en);
  };

  const openDetails = () => {
    if (onOpen) onOpen(en);
  };

  return (
    <div className="word-card__box">
      <div
        className="card word-card__button"
        role="button"
        tabIndex={0}
        aria-label={`Подробнее о слове ${en}`}
        onClick={openDetails}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            openDetails();
          }
        }}
      >
        <div className="card-body d-flex align-items-center justify-content-between gap-3 py-2 px-3">
          <span className="word-card-en">{en}</span>

          {showAction && (
            <div className="word-card-add__box">
              <div
                className={
                  canDelete
                    ? 'word-card-action--delete__shadow'
                    : 'word-card-add__shadow'
                }
              />
              {canDelete ? (
                <button
                  type="button"
                  className="word-card-action--delete"
                  aria-label={`Удалить ${en} из банки`}
                  title="Удалить из банки"
                  disabled={actionDisabled}
                  onClick={(e) => runAction(e, onDelete)}
                >
                  <DeleteIcon />
                </button>
              ) : (
                <button
                  type="button"
                  className="word-card-add__btn"
                  aria-label={`Добавить ${en} в банку`}
                  title="Добавить в банку"
                  disabled={actionDisabled}
                  onClick={(e) => runAction(e, onAddToJar)}
                >
                  <PlusIcon />
                </button>
              )}
            </div>
          )}
        </div>
      </div>
      <div className="card word-card__shadow" />
    </div>
  );
}

export default WordCard;