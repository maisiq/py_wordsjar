import { Modal } from 'react-bootstrap';

function DeleteWordModal({ word, busy = false, onHide, onConfirm }) {
  return (
    <Modal
      show={Boolean(word)}
      onHide={busy ? undefined : onHide}
      backdrop={busy ? 'static' : true}
      keyboard={!busy}
      centered
    >
      <Modal.Header closeButton={!busy}>
        <Modal.Title>Удаление слова</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        Удалить слово <strong>«{word}»</strong> из банки?
      </Modal.Body>
      <Modal.Footer>
        <button
          type="button"
          className="btn btn-modal-secondary"
          onClick={onHide}
          disabled={busy}
        >
          Отмена
        </button>
        <button
          type="button"
          className="btn btn-modal-danger"
          onClick={onConfirm}
          disabled={busy}
        >
          {busy ? 'Удаление...' : 'Удалить'}
        </button>
      </Modal.Footer>
    </Modal>
  );
}

export default DeleteWordModal;