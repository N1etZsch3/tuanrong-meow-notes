import { request } from "@/services/request";
import { API_ENDPOINTS, compactApiParams } from "@/api/routes";

export interface MedicineCategoryDto {
  id: string;
  name: string;
  code: string | null;
  description?: string | null;
  sort_order: number;
  is_enabled: boolean;
}

export interface MedicineCategoryListResponse {
  items: MedicineCategoryDto[];
}

export interface MedicineHolderBriefDto {
  holding_id: string;
  holder_id: string;
  holder_nickname: string;
  holder_avatar_url: string | null;
  current_quantity: number;
  unit: string;
  status: string;
  is_current_user_holder: boolean;
}

export interface MedicineListItemDto {
  medicine_id: string;
  name: string;
  category: { id: string; name: string } | null;
  specification: string | null;
  unit: string;
  description: string | null;
  cover_image_url: string | null;
  photo_urls?: string[];
  status: string;
  total_current_quantity: number;
  total_in_quantity: number;
  holder_count: number;
  stock_status: string;
  stock_status_label: string;
  last_operation_at: string | null;
  holders: MedicineHolderBriefDto[];
}

export interface MedicineListResponse {
  items: MedicineListItemDto[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
}

export interface MedicineListQuery {
  keyword?: string;
  category_id?: string | null;
  holding_relation?: "all" | "mine" | "others";
  sort_by?: string;
  sort_order?: "asc" | "desc";
  include_archived?: boolean;
  page?: number;
  page_size?: number;
}

export interface MedicineCatalogPayload {
  name: string;
  category_id?: string | null;
  category_name?: string | null;
  specification?: string | null;
  unit: string;
  description?: string | null;
  usage_notes?: string | null;
  cover_image_url?: string | null;
  photo_urls?: string[];
}

export interface MedicineSearchItemDto extends MedicineCatalogPayload {
  medicine_id: string;
  category?: { id: string; name: string } | null;
  category_name?: string | null;
}

export interface MedicineCreatePayload {
  medicine_id?: string | null;
  catalog?: MedicineCatalogPayload | null;
  holder_id?: string | null;
  initial_quantity: number;
  remark?: string | null;
}

export interface MedicineCreateResponse {
  medicine_id: string;
  holding_id: string;
  created_catalog: boolean;
  created_holding: boolean;
  initial_stock_log_id: string;
}

export interface MedicineCatalogUpdatePayload {
  name?: string | null;
  category_id?: string | null;
  category_name?: string | null;
  specification?: string | null;
  unit?: string | null;
  description?: string | null;
  usage_notes?: string | null;
  cover_image_url?: string | null;
  photo_urls?: string[] | null;
}

export interface MedicineCatalogUpdateResponse {
  medicine_id: string;
  updated_at: string;
}

export interface MedicineStockLogDto {
  id: string;
  medicine_id: string;
  holding_id: string | null;
  operation_type: string;
  operation_label: string;
  operator: { id: string; nickname: string; avatar_url?: string | null } | null;
  quantity_delta: number;
  quantity_before: number;
  quantity_after: number;
  unit: string;
  reason_type: string | null;
  reason_text: string | null;
  description: string | null;
  related_task: unknown | null;
  created_at: string;
}

export interface MedicineStockLogListResponse {
  items: MedicineStockLogDto[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
}

export interface MedicinePaginationQuery {
  page?: number;
  page_size?: number;
}

export interface MedicineDetailDto extends MedicineListItemDto {
  description: string | null;
  usage_notes: string | null;
  recent_logs: MedicineStockLogDto[];
  permissions: {
    can_edit_catalog: boolean;
    can_archive: boolean;
    can_delete: boolean;
  };
}

export interface MedicineHoldingDetailDto {
  holding_id: string;
  medicine: {
    medicine_id: string;
    name: string;
    category_name: string | null;
    specification: string | null;
    unit: string;
    description: string | null;
    usage_notes: string | null;
    cover_image_url: string | null;
  };
  holder: { id: string; nickname: string; avatar_url: string | null };
  initial_quantity: number;
  total_in_quantity: number;
  current_quantity: number;
  unit: string;
  status: string;
  stock_status: string;
  last_operation_at: string | null;
  recent_logs: MedicineStockLogDto[];
  pending_applications: MedicineUseApplicationDto[];
  permissions: {
    is_holder: boolean;
    can_record: boolean;
    can_apply: boolean;
    can_review_application: boolean;
  };
}

export interface MedicineQuantityOperationPayload {
  quantity: number;
  operated_at?: string | null;
  remark?: string | null;
}

export interface MedicinePurchasePayload extends MedicineQuantityOperationPayload {
  source?: string | null;
  unit_price?: number | null;
}

export interface MedicineUsePayload extends MedicineQuantityOperationPayload {
  reason_type?: string | null;
  reason_text: string;
  usage_description?: string | null;
  related_task_id?: string | null;
}

export interface MedicineScrapPayload extends MedicineQuantityOperationPayload {
  reason_type: string;
  reason_text: string;
}

export interface MedicineAdjustmentPayload {
  quantity: number;
  reason_text: string;
  operated_at?: string | null;
  remark?: string | null;
}

export interface MedicineDistributePayload extends MedicineQuantityOperationPayload {
  target_user_id: string;
}

export interface MedicineTransferPayload {
  target_user_id: string;
  reason: string;
  operated_at?: string | null;
}

export interface MedicineOperationResponse {
  holding_id?: string;
  current_quantity?: number;
  total_in_quantity?: number;
  stock_log_id?: string;
  source_holding_id?: string;
  target_holding_id?: string;
  source_current_quantity?: number;
  target_current_quantity?: number;
  transferred_quantity?: number;
  out_log_id?: string;
  in_log_id?: string;
}

export interface MedicineApplicationCreatePayload {
  quantity: number;
  reason_type?: string | null;
  reason_text: string;
  usage_description?: string | null;
  requested_use_at?: string | null;
  related_task_id?: string | null;
  remark?: string | null;
}

export interface MedicineUseApplicationDto {
  id: string;
  medicine_id: string;
  medicine_name: string;
  holding_id: string;
  quantity: number;
  unit: string;
  reason_text: string;
  usage_description: string | null;
  status: string;
  expires_at: string;
  created_at: string;
}

export interface MedicineApplicationCreateResponse {
  application_id: string;
  status: string;
  expires_at: string;
}

export interface MedicineApplicationReviewPayload {
  review_comment?: string | null;
  operated_at?: string | null;
}

export interface MedicineApplicationStatusResponse {
  application_id: string;
  status: string;
  holding_id?: string;
  current_quantity?: number;
  stock_log_id?: string;
}

export interface MedicineApplicationListQuery extends MedicinePaginationQuery {
  scope?: "mine" | "review" | "all";
  status?: string;
}

export interface MedicineApplicationDto {
  application_id: string;
  medicine: {
    medicine_id: string;
    name: string;
    specification: string | null;
    unit: string;
  };
  holding: {
    holding_id: string;
    holder: { id: string; nickname: string; avatar_url?: string | null } | null;
    current_quantity: number;
    unit: string;
  };
  applicant: { id: string; nickname: string; avatar_url?: string | null } | null;
  holder: { id: string; nickname: string; avatar_url?: string | null } | null;
  quantity: number;
  unit: string;
  reason_type: string | null;
  reason_text: string;
  usage_description: string | null;
  requested_use_at: string | null;
  related_task: unknown | null;
  status: string;
  review_comment: string | null;
  reviewed_at: string | null;
  expires_at: string;
  created_at: string;
  updated_at: string | null;
}

export interface MedicineApplicationListResponse {
  items: MedicineApplicationDto[];
  page: number;
  page_size: number;
  total: number;
  has_more: boolean;
}

export function getMedicineCategories(
  accessToken: string,
): Promise<MedicineCategoryListResponse> {
  return request<MedicineCategoryListResponse>({
    url: API_ENDPOINTS.medicineCategories,
    method: "GET",
    token: accessToken,
  });
}

export function getMedicines(
  accessToken: string,
  query: MedicineListQuery = {},
): Promise<MedicineListResponse> {
  return request<MedicineListResponse>({
    url: API_ENDPOINTS.medicines.list,
    method: "GET",
    data: compactApiParams(query),
    token: accessToken,
  });
}

export function searchMedicines(
  accessToken: string,
  keyword: string,
): Promise<{ items: MedicineSearchItemDto[] }> {
  return request({
    url: API_ENDPOINTS.medicines.search,
    method: "GET",
    data: compactApiParams({ keyword }),
    token: accessToken,
  });
}

export function createMedicine(
  accessToken: string,
  payload: MedicineCreatePayload,
): Promise<MedicineCreateResponse> {
  return request<MedicineCreateResponse, MedicineCreatePayload & Record<string, unknown>>({
    url: API_ENDPOINTS.medicines.list,
    method: "POST",
    data: { ...payload },
    token: accessToken,
  });
}

export function updateMedicineCatalog(
  accessToken: string,
  medicineId: string,
  payload: MedicineCatalogUpdatePayload,
): Promise<MedicineCatalogUpdateResponse> {
  return request<
    MedicineCatalogUpdateResponse,
    MedicineCatalogUpdatePayload & Record<string, unknown>
  >({
    url: API_ENDPOINTS.admin.medicine(medicineId),
    method: "PATCH",
    data: { ...payload },
    token: accessToken,
  });
}

export function getMedicineDetail(
  accessToken: string,
  medicineId: string,
): Promise<MedicineDetailDto> {
  return request<MedicineDetailDto>({
    url: API_ENDPOINTS.medicines.detail(medicineId),
    method: "GET",
    token: accessToken,
  });
}

export function getMedicineLogs(
  accessToken: string,
  medicineId: string,
  query: MedicinePaginationQuery = {},
): Promise<MedicineStockLogListResponse> {
  return request<MedicineStockLogListResponse>({
    url: API_ENDPOINTS.medicines.logs(medicineId),
    method: "GET",
    data: compactApiParams(query),
    token: accessToken,
  });
}

export function getMedicineHoldingDetail(
  accessToken: string,
  holdingId: string,
): Promise<MedicineHoldingDetailDto> {
  return request<MedicineHoldingDetailDto>({
    url: API_ENDPOINTS.medicineHoldings.detail(holdingId),
    method: "GET",
    token: accessToken,
  });
}

export function getMedicineHoldingLogs(
  accessToken: string,
  holdingId: string,
  query: MedicinePaginationQuery = {},
): Promise<MedicineStockLogListResponse> {
  return request<MedicineStockLogListResponse>({
    url: API_ENDPOINTS.medicineHoldings.logs(holdingId),
    method: "GET",
    data: compactApiParams(query),
    token: accessToken,
  });
}

export function recordMedicinePurchase(
  accessToken: string,
  holdingId: string,
  payload: MedicinePurchasePayload,
): Promise<MedicineOperationResponse> {
  return request<MedicineOperationResponse, MedicinePurchasePayload & Record<string, unknown>>({
    url: API_ENDPOINTS.medicineHoldings.purchase(holdingId),
    method: "POST",
    data: { ...payload },
    token: accessToken,
  });
}

export function recordMedicineUse(
  accessToken: string,
  holdingId: string,
  payload: MedicineUsePayload,
): Promise<MedicineOperationResponse> {
  return request<MedicineOperationResponse, MedicineUsePayload & Record<string, unknown>>({
    url: API_ENDPOINTS.medicineHoldings.use(holdingId),
    method: "POST",
    data: { ...payload },
    token: accessToken,
  });
}

export function recordMedicineScrap(
  accessToken: string,
  holdingId: string,
  payload: MedicineScrapPayload,
): Promise<MedicineOperationResponse> {
  return request<MedicineOperationResponse, MedicineScrapPayload & Record<string, unknown>>({
    url: API_ENDPOINTS.medicineHoldings.scrap(holdingId),
    method: "POST",
    data: { ...payload },
    token: accessToken,
  });
}

export function recordMedicineAdjustment(
  accessToken: string,
  holdingId: string,
  payload: MedicineAdjustmentPayload,
): Promise<MedicineOperationResponse> {
  return request<
    MedicineOperationResponse,
    MedicineAdjustmentPayload & Record<string, unknown>
  >({
    url: API_ENDPOINTS.medicineHoldings.adjust(holdingId),
    method: "POST",
    data: { ...payload },
    token: accessToken,
  });
}

export function distributeMedicine(
  accessToken: string,
  holdingId: string,
  payload: MedicineDistributePayload,
): Promise<MedicineOperationResponse> {
  return request<MedicineOperationResponse, MedicineDistributePayload & Record<string, unknown>>({
    url: API_ENDPOINTS.medicineHoldings.distribute(holdingId),
    method: "POST",
    data: { ...payload },
    token: accessToken,
  });
}

export function transferMedicine(
  accessToken: string,
  holdingId: string,
  payload: MedicineTransferPayload,
): Promise<MedicineOperationResponse> {
  return request<MedicineOperationResponse, MedicineTransferPayload & Record<string, unknown>>({
    url: API_ENDPOINTS.medicineHoldings.transfer(holdingId),
    method: "POST",
    data: { ...payload },
    token: accessToken,
  });
}

export function createMedicineApplication(
  accessToken: string,
  holdingId: string,
  payload: MedicineApplicationCreatePayload,
): Promise<MedicineApplicationCreateResponse> {
  return request<
    MedicineApplicationCreateResponse,
    MedicineApplicationCreatePayload & Record<string, unknown>
  >({
    url: API_ENDPOINTS.medicineHoldings.applications(holdingId),
    method: "POST",
    data: { ...payload },
    token: accessToken,
  });
}

export function getMedicineApplications(
  accessToken: string,
  query: MedicineApplicationListQuery = {},
): Promise<MedicineApplicationListResponse> {
  return request<MedicineApplicationListResponse>({
    url: API_ENDPOINTS.medicineApplications.list,
    method: "GET",
    data: compactApiParams(query),
    token: accessToken,
  });
}

export function getMedicineApplicationDetail(
  accessToken: string,
  applicationId: string,
): Promise<MedicineApplicationDto> {
  return request<MedicineApplicationDto>({
    url: API_ENDPOINTS.medicineApplications.detail(applicationId),
    method: "GET",
    token: accessToken,
  });
}

export function approveMedicineApplication(
  accessToken: string,
  applicationId: string,
  payload: MedicineApplicationReviewPayload,
): Promise<MedicineApplicationStatusResponse> {
  return request<
    MedicineApplicationStatusResponse,
    MedicineApplicationReviewPayload & Record<string, unknown>
  >({
    url: API_ENDPOINTS.medicineApplications.approve(applicationId),
    method: "POST",
    data: { ...payload },
    token: accessToken,
  });
}

export function rejectMedicineApplication(
  accessToken: string,
  applicationId: string,
  payload: { review_comment: string },
): Promise<MedicineApplicationStatusResponse> {
  return request<MedicineApplicationStatusResponse, { review_comment: string }>({
    url: API_ENDPOINTS.medicineApplications.reject(applicationId),
    method: "POST",
    data: payload,
    token: accessToken,
  });
}

export function cancelMedicineApplication(
  accessToken: string,
  applicationId: string,
  payload: { cancel_reason?: string | null },
): Promise<MedicineApplicationStatusResponse> {
  return request<MedicineApplicationStatusResponse, { cancel_reason?: string | null }>({
    url: API_ENDPOINTS.medicineApplications.cancel(applicationId),
    method: "POST",
    data: payload,
    token: accessToken,
  });
}
