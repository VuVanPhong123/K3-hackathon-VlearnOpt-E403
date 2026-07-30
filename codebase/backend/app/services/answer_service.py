from __future__ import annotations

from collections.abc import AsyncIterator

from app.config import settings
from app.schemas import ChatHistoryItem
from app.services.provider_gateway import ProviderGateway
from app.services.providers.base import ProviderResult, ProviderStreamChunk


GENERAL_CHAT_PROMPT = (
    "Bạn là VLearn Tutor, một trợ lý học tập thân thiện. "
    "Hãy trả lời bằng tiếng Việt rõ ràng, có cấu trúc và phù hợp với câu hỏi. "
    "Không tự nhận rằng câu trả lời đến từ tài liệu nếu người dùng chưa mở tài liệu phù hợp."
)

PAGE_CHAT_PROMPT = (
    "Bạn là VLearn Tutor. Người dùng đang hỏi về một trang PDF cụ thể.\n"
    "Bạn nhận được cả ảnh render của trang và phần văn bản trích xuất.\n"
    "Hãy quan sát trực tiếp hình ảnh để hiểu bảng, hình, biểu đồ, sơ đồ, công thức và bố cục.\n"
    "Chỉ trả lời dựa trên nội dung thật sự nhìn thấy ở trang này. "
    "Không dùng trí nhớ về một tài liệu nổi tiếng để đoán nội dung trang. "
    "Nếu không nhìn thấy đối tượng người dùng hỏi, hãy nói rõ. "
    "Trả lời bằng tiếng Việt, có cấu trúc và dễ hiểu."
)

VISUAL_REGION_PROMPT = (
    "Bạn là VLearn Tutor. Người dùng đã khoanh một vùng cụ thể trên một trang PDF. "
    "Hình ảnh đính kèm chính là vùng được chọn. "
    "Chỉ phân tích những gì thật sự nhìn thấy trong vùng này, kết hợp với văn bản giao với vùng nếu có. "
    "Nếu đây là bảng, hãy xác định tiêu đề, hàng, cột và khác biệt quan trọng. "
    "Nếu đây là biểu đồ, hãy xác định trục, xu hướng, điểm nổi bật và kết luận. "
    "Nếu đây là sơ đồ, hãy giải thích các khối, luồng dữ liệu và quan hệ giữa các thành phần. "
    "Nếu vùng quá mơ hồ hoặc không đủ thông tin, hãy nói rõ. Không đoán dựa trên tên tài liệu."
)

SELECTION_PROMPT = (
    "Bạn là VLearn Tutor. Người dùng đã bôi đen một đoạn văn bản thật trên PDF. "
    "Hãy giải thích dựa trên đoạn được chọn và ngữ cảnh xung quanh. "
    "Không thêm nội dung không có trong tài liệu."
)

DOCUMENT_SEARCH_PROMPT = (
    "Bạn là VLearn Tutor. Hãy trả lời dựa trên bằng chứng trích xuất từ tài liệu PDF. "
    "Câu hỏi có thể là yêu cầu định nghĩa hoặc giải thích một thuật ngữ. "
    "Nếu tài liệu không có câu định nghĩa trực tiếp dạng 'X là...', hãy tổng hợp từ các đoạn mô tả chức năng, cấu trúc, cách hoạt động hoặc ví dụ trong bằng chứng. "
    "Chỉ suy luận trong phạm vi bằng chứng được cung cấp; không dùng kiến thức ngoài tài liệu khi người dùng đang hỏi theo tài liệu. "
    "Nếu bằng chứng chỉ nhắc tên thuật ngữ mà không giải thích đủ, hãy nói rõ giới hạn đó. "
    "Nếu bằng chứng không đủ, hãy nói rõ không tìm thấy đủ thông tin, nhưng không nói rằng đã kiểm tra toàn bộ tài liệu. "
    "Không đoán nội dung hình, bảng hoặc biểu đồ nếu không có bằng chứng hoặc hình ảnh được cung cấp."
)


class AnswerService:
    def __init__(self, provider_gateway: ProviderGateway | None = None) -> None:
        self.provider_gateway = provider_gateway or ProviderGateway()

    @staticmethod
    def _history(history: list[ChatHistoryItem]) -> list[dict[str, str]]:
        return [
            {"role": item.role, "content": item.content}
            for item in history[-settings.chat_recent_message_limit:]
        ]

    @staticmethod
    def page_prompt(*, message: str, filename: str, page_number: int, page_text: str) -> str:
        return (
            f"Tên tài liệu: {filename}\n"
            f"Trang PDF: {page_number}\n\n"
            "Văn bản trích xuất:\n"
            "--- VĂN BẢN TRANG ---\n"
            f"{page_text or '(Trang này có ít văn bản trích xuất; hãy dựa vào hình ảnh trang.)'}\n"
            "--- KẾT THÚC VĂN BẢN TRANG ---\n\n"
            f"Câu hỏi:\n{message}\n\n"
            f"Quy tắc: trích dẫn luôn là trang {page_number}."
        )

    @staticmethod
    def visual_region_prompt(
        *,
        message: str,
        filename: str,
        page_number: int,
        overlapping_text: str,
    ) -> str:
        return (
            f"Tên tài liệu: {filename}\n"
            f"Trang PDF: {page_number}\n\n"
            "Văn bản giao với vùng được chọn:\n"
            "--- VĂN BẢN TRONG VÙNG ---\n"
            f"{overlapping_text or '(Không có văn bản giao với vùng.)'}\n"
            "--- KẾT THÚC VĂN BẢN TRONG VÙNG ---\n\n"
            f"Câu hỏi:\n{message}"
        )

    @staticmethod
    def selection_prompt_content(
        *,
        message: str,
        filename: str,
        page_number: int,
        selected_text: str,
        surrounding_text: str,
    ) -> str:
        return (
            f"Tên tài liệu: {filename}\n"
            f"Trang PDF: {page_number}\n\n"
            "Đoạn được chọn:\n"
            "--- VĂN BẢN ĐƯỢC CHỌN ---\n"
            f"{selected_text}\n"
            "--- KẾT THÚC VĂN BẢN ĐƯỢC CHỌN ---\n\n"
            "Ngữ cảnh xung quanh:\n"
            "--- NGỮ CẢNH ---\n"
            f"{surrounding_text}\n"
            "--- KẾT THÚC NGỮ CẢNH ---\n\n"
            f"Câu hỏi:\n{message}"
        )

    @staticmethod
    def document_search_prompt_content(*, message: str, filename: str, evidence_text: str) -> str:
        return (
            f"Tên tài liệu: {filename}\n\n"
            "Bằng chứng tìm được:\n"
            "--- BẰNG CHỨNG ---\n"
            f"{evidence_text}\n"
            "--- KẾT THÚC BẰNG CHỨNG ---\n\n"
            f"Câu hỏi:\n{message}"
        )

    @staticmethod
    def document_visual_search_prompt(
        *,
        message: str,
        filename: str,
        page_number: int,
        page_text: str,
        extra_evidence: str,
    ) -> str:
        return (
            f"Tên tài liệu: {filename}\n"
            f"Trang PDF ứng viên phù hợp nhất: {page_number}\n\n"
            "Văn bản của trang/chú thích hình:\n"
            "--- VĂN BẢN TRANG ---\n"
            f"{page_text}\n"
            "--- KẾT THÚC VĂN BẢN TRANG ---\n\n"
            "Bằng chứng bổ sung từ tìm kiếm:\n"
            "--- BẰNG CHỨNG BỔ SUNG ---\n"
            f"{extra_evidence or '(Không có)'}\n"
            "--- KẾT THÚC BẰNG CHỨNG BỔ SUNG ---\n\n"
            f"Câu hỏi:\n{message}"
        )

    async def answer_general(
        self,
        *,
        message: str,
        history: list[ChatHistoryItem],
    ) -> tuple[ProviderResult, bool]:
        messages = [*self._history(history), {"role": "user", "content": message}]
        return await self.provider_gateway.generate(system_prompt=GENERAL_CHAT_PROMPT, messages=messages)

    async def stream_general(
        self,
        *,
        message: str,
        history: list[ChatHistoryItem],
    ) -> AsyncIterator[ProviderStreamChunk]:
        messages = [*self._history(history), {"role": "user", "content": message}]
        async for chunk in self.provider_gateway.stream_generate(
            system_prompt=GENERAL_CHAT_PROMPT,
            messages=messages,
        ):
            yield chunk

    async def answer_page(
        self,
        *,
        message: str,
        history: list[ChatHistoryItem],
        filename: str,
        page_number: int,
        page_text: str,
        image_bytes: bytes,
        mime_type: str = "image/png",
    ) -> tuple[ProviderResult, bool]:
        return await self.provider_gateway.generate_multimodal(
            system_prompt=PAGE_CHAT_PROMPT,
            text_prompt=self.page_prompt(
                message=message,
                filename=filename,
                page_number=page_number,
                page_text=page_text,
            ),
            image_bytes=image_bytes,
            mime_type=mime_type,
            history=self._history(history),
        )

    async def stream_page(
        self,
        *,
        message: str,
        history: list[ChatHistoryItem],
        filename: str,
        page_number: int,
        page_text: str,
        image_bytes: bytes,
        mime_type: str = "image/png",
    ) -> AsyncIterator[ProviderStreamChunk]:
        async for chunk in self.provider_gateway.stream_generate_multimodal(
            system_prompt=PAGE_CHAT_PROMPT,
            text_prompt=self.page_prompt(
                message=message,
                filename=filename,
                page_number=page_number,
                page_text=page_text,
            ),
            image_bytes=image_bytes,
            mime_type=mime_type,
            history=self._history(history),
        ):
            yield chunk

    async def answer_visual_region(
        self,
        *,
        message: str,
        history: list[ChatHistoryItem],
        filename: str,
        page_number: int,
        overlapping_text: str,
        image_bytes: bytes,
        mime_type: str = "image/png",
    ) -> tuple[ProviderResult, bool]:
        return await self.provider_gateway.generate_multimodal(
            system_prompt=VISUAL_REGION_PROMPT,
            text_prompt=self.visual_region_prompt(
                message=message,
                filename=filename,
                page_number=page_number,
                overlapping_text=overlapping_text,
            ),
            image_bytes=image_bytes,
            mime_type=mime_type,
            history=self._history(history),
        )

    async def stream_visual_region(
        self,
        *,
        message: str,
        history: list[ChatHistoryItem],
        filename: str,
        page_number: int,
        overlapping_text: str,
        image_bytes: bytes,
        mime_type: str = "image/png",
    ) -> AsyncIterator[ProviderStreamChunk]:
        async for chunk in self.provider_gateway.stream_generate_multimodal(
            system_prompt=VISUAL_REGION_PROMPT,
            text_prompt=self.visual_region_prompt(
                message=message,
                filename=filename,
                page_number=page_number,
                overlapping_text=overlapping_text,
            ),
            image_bytes=image_bytes,
            mime_type=mime_type,
            history=self._history(history),
        ):
            yield chunk

    async def answer_selection(
        self,
        *,
        message: str,
        history: list[ChatHistoryItem],
        filename: str,
        page_number: int,
        selected_text: str,
        surrounding_text: str,
    ) -> tuple[ProviderResult, bool]:
        content = self.selection_prompt_content(
            message=message,
            filename=filename,
            page_number=page_number,
            selected_text=selected_text,
            surrounding_text=surrounding_text,
        )
        messages = [*self._history(history), {"role": "user", "content": content}]
        return await self.provider_gateway.generate(system_prompt=SELECTION_PROMPT, messages=messages)

    async def stream_selection(
        self,
        *,
        message: str,
        history: list[ChatHistoryItem],
        filename: str,
        page_number: int,
        selected_text: str,
        surrounding_text: str,
    ) -> AsyncIterator[ProviderStreamChunk]:
        content = self.selection_prompt_content(
            message=message,
            filename=filename,
            page_number=page_number,
            selected_text=selected_text,
            surrounding_text=surrounding_text,
        )
        messages = [*self._history(history), {"role": "user", "content": content}]
        async for chunk in self.provider_gateway.stream_generate(
            system_prompt=SELECTION_PROMPT,
            messages=messages,
        ):
            yield chunk

    async def answer_document_search(
        self,
        *,
        message: str,
        history: list[ChatHistoryItem],
        filename: str,
        evidence_text: str,
    ) -> tuple[ProviderResult, bool]:
        content = self.document_search_prompt_content(
            message=message,
            filename=filename,
            evidence_text=evidence_text,
        )
        messages = [*self._history(history), {"role": "user", "content": content}]
        return await self.provider_gateway.generate(system_prompt=DOCUMENT_SEARCH_PROMPT, messages=messages)

    async def stream_document_search(
        self,
        *,
        message: str,
        history: list[ChatHistoryItem],
        filename: str,
        evidence_text: str,
    ) -> AsyncIterator[ProviderStreamChunk]:
        content = self.document_search_prompt_content(
            message=message,
            filename=filename,
            evidence_text=evidence_text,
        )
        messages = [*self._history(history), {"role": "user", "content": content}]
        async for chunk in self.provider_gateway.stream_generate(
            system_prompt=DOCUMENT_SEARCH_PROMPT,
            messages=messages,
        ):
            yield chunk

    async def answer_document_visual_search(
        self,
        *,
        message: str,
        history: list[ChatHistoryItem],
        filename: str,
        page_number: int,
        page_text: str,
        extra_evidence: str,
        image_bytes: bytes,
        mime_type: str = "image/png",
    ) -> tuple[ProviderResult, bool]:
        return await self.provider_gateway.generate_multimodal(
            system_prompt=PAGE_CHAT_PROMPT,
            text_prompt=self.document_visual_search_prompt(
                message=message,
                filename=filename,
                page_number=page_number,
                page_text=page_text,
                extra_evidence=extra_evidence,
            ),
            image_bytes=image_bytes,
            mime_type=mime_type,
            history=self._history(history),
        )

    async def stream_document_visual_search(
        self,
        *,
        message: str,
        history: list[ChatHistoryItem],
        filename: str,
        page_number: int,
        page_text: str,
        extra_evidence: str,
        image_bytes: bytes,
        mime_type: str = "image/png",
    ) -> AsyncIterator[ProviderStreamChunk]:
        async for chunk in self.provider_gateway.stream_generate_multimodal(
            system_prompt=PAGE_CHAT_PROMPT,
            text_prompt=self.document_visual_search_prompt(
                message=message,
                filename=filename,
                page_number=page_number,
                page_text=page_text,
                extra_evidence=extra_evidence,
            ),
            image_bytes=image_bytes,
            mime_type=mime_type,
            history=self._history(history),
        ):
            yield chunk
