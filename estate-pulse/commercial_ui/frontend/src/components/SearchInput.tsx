type SearchInputProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
};

export function SearchInput({ value, onChange, onSubmit, disabled = false }: SearchInputProps) {
  return (
    <form
      className="ep-searchbar"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <label className="ep-searchbar__label ep-visually-hidden" htmlFor="search-home-query">
        단지명 또는 주소
      </label>
      <div className="ep-searchbar__controls">
        <input
          id="search-home-query"
          type="search"
          className="ep-searchbar__input"
          placeholder="단지명이나 주소를 입력하세요"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          disabled={disabled}
        />
        <button className="ep-button ep-button--primary" type="submit" disabled={disabled}>
          분석 시작
        </button>
      </div>
    </form>
  );
}
