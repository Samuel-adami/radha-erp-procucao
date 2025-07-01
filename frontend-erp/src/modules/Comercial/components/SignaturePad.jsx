import React, { useRef } from 'react';
import SignatureCanvas from 'react-signature-canvas';

function SignaturePad({ onChange }) {
  const ref = useRef(null);

  const handleEnd = () => {
    const data = ref.current?.toDataURL();
    if (onChange) onChange(data);
  };

  const clear = () => {
    ref.current?.clear();
    handleEnd();
  };

  return (
    <div className="space-y-2">
      <SignatureCanvas
        ref={ref}
        penColor="black"
        canvasProps={{ width: 300, height: 150, className: 'border' }}
        onEnd={handleEnd}
      />
      <button type="button" onClick={clear} className="text-blue-600 underline">
        Limpar
      </button>
    </div>
  );
}

export default SignaturePad;
