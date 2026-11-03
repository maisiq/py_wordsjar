import Dropdown from 'react-bootstrap/Dropdown';

function SortIcon() {
  return (
    <svg
      className="sort-dropdown__icon"
      viewBox="0 0 16 16"
      aria-hidden="true"
      focusable="false"
    >
      <path d="M11.5 15a.5.5 0 0 0 .5-.5V2.707l3.146 3.147a.5.5 0 0 0 .708-.708l-4-4a.5.5 0 0 0-.708 0l-4 4a.5.5 0 1 0 .708.708L11 2.707V14.5a.5.5 0 0 0 .5.5m-7-14a.5.5 0 0 1 .5.5v11.793l3.146-3.147a.5.5 0 0 1 .708.708l-4 4a.5.5 0 0 1-.708 0l-4-4a.5.5 0 0 1 .708-.708L4 13.293V1.5a.5.5 0 0 1 .5-.5" />
    </svg>
  );
}

/**
 * Кнопка с выпадающим списком вариантов сортировки.
 *
 * options: [{ key, label }] — порядок пунктов в меню;
 * value: key выбранного варианта;
 * onChange(key) вызывается при выборе пункта.
 */
function SortDropdown({
  options,
  value,
  onChange,
  label = 'Сортировка',
  disabled = false,
}) {
  const current = options.find((option) => option.key === value) || options[0];

  return (
    <Dropdown align="end" className="sort-dropdown">
      <Dropdown.Toggle
        id="jar-sort-toggle"
        variant="outline-primary"
        size="sm"
        className="sort-dropdown__toggle"
        disabled={disabled}
        title={label}
        aria-label={`${label}: ${current ? current.label : ''}`}
      >
        <SortIcon />
      </Dropdown.Toggle>

      <Dropdown.Menu className="sort-dropdown__menu">
        {options.map((option) => (
          <Dropdown.Item
            key={option.key}
            as="button"
            type="button"
            className="sort-dropdown__item"
            active={option.key === value}
            onClick={() => onChange(option.key)}
          >
            {option.label}
          </Dropdown.Item>
        ))}
      </Dropdown.Menu>
    </Dropdown>
  );
}

export default SortDropdown;
