// mautrix-signal - A Matrix-signal puppeting bridge.
// Copyright (C) 2023 Scott Weber
// Copyright (C) 2025 Tulir Asokan
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

package libsignalgo

/*
#include "./libsignal-ffi.h"
*/
import "C"
import (
	"context"
	"runtime"

	"github.com/google/uuid"
)

type SealedSenderAddress struct {
	E164     string
	UUID     uuid.UUID
	DeviceID uint32
}

func NewSealedSenderAddress(e164 string, uuid uuid.UUID, deviceID uint32) *SealedSenderAddress {
	return &SealedSenderAddress{
		E164:     e164,
		UUID:     uuid,
		DeviceID: deviceID,
	}
}

func SealedSenderEncryptPlaintext(ctx context.Context, message []byte, contentHint UnidentifiedSenderMessageContentHint, forAddress *Address, fromSenderCert *SenderCertificate, sessionStore SessionStore, identityStore IdentityKeyStore) ([]byte, error) {
	ciphertextMessage, err := Encrypt(ctx, message, forAddress, sessionStore, identityStore)
	if err != nil {
		return nil, err
	}

	usmc, err := NewUnidentifiedSenderMessageContent(
		ciphertextMessage,
		fromSenderCert,
		contentHint,
		nil,
	)
	if err != nil {
		return nil, err
	}
	return SealedSenderEncrypt(ctx, usmc, forAddress, identityStore)
}

func SealedSenderEncrypt(ctx context.Context, usmc *UnidentifiedSenderMessageContent, forRecipient *Address, identityStore IdentityKeyStore) ([]byte, error) {
	var encrypted C.SignalOwnedBuffer = C.SignalOwnedBuffer{}
	callbackCtx := NewCallbackContext(ctx)
	defer callbackCtx.Unref()
	signalFfiError := C.signal_sealed_session_cipher_encrypt(
		&encrypted,
		forRecipient.constPtr(),
		usmc.constPtr(),
		callbackCtx.wrapIdentityKeyStore(identityStore),
	)
	runtime.KeepAlive(usmc)
	runtime.KeepAlive(forRecipient)
	if signalFfiError != nil {
		return nil, callbackCtx.wrapError(signalFfiError)
	}
	return CopySignalOwnedBufferToBytes(encrypted), nil
}

func SealedSenderMultiRecipientEncrypt(messageContent *UnidentifiedSenderMessageContent, forRecipients []*Address, identityStore IdentityKeyStore, sessionStore SessionStore, ctx *CallbackContext) ([]byte, error) {
	panic("not implemented")
}

type SealedSenderResult struct {
	Message []byte
	Sender  SealedSenderAddress
}

func SealedSenderDecryptToUSMC(
	ctx context.Context,
	ciphertext []byte,
	identityStore IdentityKeyStore,
) (*UnidentifiedSenderMessageContent, error) {
	callbackCtx := NewCallbackContext(ctx)
	defer callbackCtx.Unref()
	var usmc C.SignalMutPointerUnidentifiedSenderMessageContent
	signalFfiError := C.signal_sealed_session_cipher_decrypt_to_usmc(
		&usmc,
		BytesToBuffer(ciphertext),
		callbackCtx.wrapIdentityKeyStore(identityStore),
	)
	runtime.KeepAlive(ciphertext)
	if signalFfiError != nil {
		return nil, callbackCtx.wrapError(signalFfiError)
	}
	return wrapUnidentifiedSenderMessageContent(usmc.raw), nil
}

type UnidentifiedSenderMessageContentHint uint32

const (
	UnidentifiedSenderMessageContentHintDefault    UnidentifiedSenderMessageContentHint = 0
	UnidentifiedSenderMessageContentHintResendable UnidentifiedSenderMessageContentHint = 1
	UnidentifiedSenderMessageContentHintImplicit   UnidentifiedSenderMessageContentHint = 2
)

type UnidentifiedSenderMessageContent struct {
	nc  noCopy
	ptr *C.SignalUnidentifiedSenderMessageContent
}

func wrapUnidentifiedSenderMessageContent(ptr *C.SignalUnidentifiedSenderMessageContent) *UnidentifiedSenderMessageContent {
	messageContent := &UnidentifiedSenderMessageContent{ptr: ptr}
	runtime.SetFinalizer(messageContent, (*UnidentifiedSenderMessageContent).Destroy)
	return messageContent
}

func NewUnidentifiedSenderMessageContent(message *CiphertextMessage, senderCertificate *SenderCertificate, contentHint UnidentifiedSenderMessageContentHint, groupID []byte) (*UnidentifiedSenderMessageContent, error) {
	var usmc C.SignalMutPointerUnidentifiedSenderMessageContent
	signalFfiError := C.signal_unidentified_sender_message_content_new(
		&usmc,
		message.constPtr(),
		senderCertificate.constPtr(),
		C.uint32_t(contentHint),
		BytesToBuffer(groupID),
	)
	runtime.KeepAlive(message)
	runtime.KeepAlive(senderCertificate)
	runtime.KeepAlive(groupID)
	if signalFfiError != nil {
		return nil, wrapError(signalFfiError)
	}
	return wrapUnidentifiedSenderMessageContent(usmc.raw), nil
}

//func NewUnidentifiedSenderMessageContentFromMessage(sealedSenderMessage []byte, identityStore IdentityKeyStore, ctx *CallbackContext) (*UnidentifiedSenderMessageContent, error) {
//	contextPtr := gopointer.Save(ctx)
//	defer gopointer.Unref(contextPtr)
//
//	var usmc *C.SignalUnidentifiedSenderMessageContent
//
//	signalFfiError := C.signal_sealed_session_cipher_decrypt_to_usmc(
//		&usmc,
//		BytesToBuffer(sealedSenderMessage),
//		wrapIdentityKeyStore(identityStore),
//		contextPtr,
//	)
//	if signalFfiError != nil {
//		return nil, wrapError(signalFfiError)
//	}
//	return wrapUnidentifiedSenderMessageContent(usmc), nil
//}

func DeserializeUnidentifiedSenderMessageContent(serialized []byte) (*UnidentifiedSenderMessageContent, error) {
	var usmc C.SignalMutPointerUnidentifiedSenderMessageContent
	signalFfiError := C.signal_unidentified_sender_message_content_deserialize(&usmc, BytesToBuffer(serialized))
	runtime.KeepAlive(serialized)
	if signalFfiError != nil {
		return nil, wrapError(signalFfiError)
	}
	return wrapUnidentifiedSenderMessageContent(usmc.raw), nil
}

func (usmc *UnidentifiedSenderMessageContent) mutPtr() C.SignalMutPointerUnidentifiedSenderMessageContent {
	return C.SignalMutPointerUnidentifiedSenderMessageContent{usmc.ptr}
}

func (usmc *UnidentifiedSenderMessageContent) constPtr() C.SignalConstPointerUnidentifiedSenderMessageContent {
	return C.SignalConstPointerUnidentifiedSenderMessageContent{usmc.ptr}
}

func (usmc *UnidentifiedSenderMessageContent) Destroy() error {
	usmc.CancelFinalizer()
	return wrapError(C.signal_unidentified_sender_message_content_destroy(usmc.mutPtr()))
}

func (usmc *UnidentifiedSenderMessageContent) CancelFinalizer() {
	runtime.SetFinalizer(usmc, nil)
}

func (usmc *UnidentifiedSenderMessageContent) Serialize() ([]byte, error) {
	var serialized C.SignalOwnedBuffer = C.SignalOwnedBuffer{}
	signalFfiError := C.signal_unidentified_sender_message_content_serialize(&serialized, usmc.constPtr())
	runtime.KeepAlive(usmc)
	if signalFfiError != nil {
		return nil, wrapError(signalFfiError)
	}
	return CopySignalOwnedBufferToBytes(serialized), nil
}

func (usmc *UnidentifiedSenderMessageContent) GetContents() ([]byte, error) {
	var contents C.SignalOwnedBuffer = C.SignalOwnedBuffer{}
	signalFfiError := C.signal_unidentified_sender_message_content_get_contents(&contents, usmc.constPtr())
	runtime.KeepAlive(usmc)
	if signalFfiError != nil {
		return nil, wrapError(signalFfiError)
	}
	return CopySignalOwnedBufferToBytes(contents), nil
}

//func (usmc *UnidentifiedSenderMessageContent) GetGroupID() ([]byte, error) {
//	var groupID *C.uchar
//	var length C.ulong
//	signalFfiError := C.signal_unidentified_sender_message_content_get_group_id(&groupID, &length, usmc.ptr)
//	if signalFfiError != nil {
//		return nil, wrapError(signalFfiError)
//	}
//	if groupID == nil {
//		return nil, nil
//	}
//	return CopyBufferToBytes(groupID, length), nil
//}

func (usmc *UnidentifiedSenderMessageContent) GetSenderCertificate() (*SenderCertificate, error) {
	var senderCertificate C.SignalMutPointerSenderCertificate
	signalFfiError := C.signal_unidentified_sender_message_content_get_sender_cert(&senderCertificate, usmc.constPtr())
	runtime.KeepAlive(usmc)
	if signalFfiError != nil {
		return nil, wrapError(signalFfiError)
	}
	return wrapSenderCertificate(senderCertificate.raw), nil
}

func (usmc *UnidentifiedSenderMessageContent) GetMessageType() (CiphertextMessageType, error) {
	var messageType C.uint8_t
	signalFfiError := C.signal_unidentified_sender_message_content_get_msg_type(&messageType, usmc.constPtr())
	runtime.KeepAlive(usmc)
	if signalFfiError != nil {
		return 0, wrapError(signalFfiError)
	}
	return CiphertextMessageType(messageType), nil
}

func (usmc *UnidentifiedSenderMessageContent) GetContentHint() (UnidentifiedSenderMessageContentHint, error) {
	var contentHint C.uint32_t
	signalFfiError := C.signal_unidentified_sender_message_content_get_content_hint(&contentHint, usmc.constPtr())
	runtime.KeepAlive(usmc)
	if signalFfiError != nil {
		return 0, wrapError(signalFfiError)
	}
	return UnidentifiedSenderMessageContentHint(contentHint), nil
}
