export function buildChatContext({ attachment, activePage }) {
  return {
    active_page: activePage || null,
    attached_pages: attachment?.type === "page" ? [attachment.pageNumber] : [],
    page_range: null,
    text_selection:
      attachment?.type === "text_selection"
        ? {
            page_number: attachment.pageNumber,
            selected_text: attachment.selectedText,
            bounding_boxes: attachment.boundingBoxes || [],
          }
        : null,
    visual_region:
      attachment?.type === "visual_region"
        ? {
            page_number: attachment.pageNumber,
            bbox: attachment.bbox,
          }
        : null,
  };
}
