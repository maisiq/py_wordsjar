import AuthButton from './AuthButton';

function SearchBar({ query = '', onQueryChange, onSearch }) {
  const submit = () => {
    const q = query.trim();
    if (onSearch) onSearch(q);
  };

  return (
    <div className="words-search mb-4">
      <svg className="words-search-icon" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85zm-5.242 1.156a5 5 0 1 1 0-10 5 5 0 0 1 0 10z" />
      </svg>
      <input
        type="text"
        className="words-search-input"
        placeholder="Поиск слов..."
        autoComplete="off"
        aria-label="Поиск слов"
        value={query}
        onChange={(e) => {
          if (onQueryChange) onQueryChange(e.target.value);
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            submit();
          }
        }}
      />
      <AuthButton />
    </div>
  );
}

export default SearchBar;
