use pyo3::prelude::*;

mod async_client;
mod client;
mod cookies;
mod errors;
mod request;
mod response;

use async_client::AsyncClient;
use client::Client;
use request::RequestBody;
use std::collections::HashMap;

#[pymodule]
fn impit(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Client>()?;
    m.add_class::<AsyncClient>()?;
    m.add_class::<response::ImpitPyResponse>()?;

    m.add("HTTPError", m.py().get_type::<errors::HTTPError>())?;
    m.add("RequestError", m.py().get_type::<errors::RequestError>())?;
    m.add(
        "TransportError",
        m.py().get_type::<errors::TransportError>(),
    )?;
    m.add(
        "TimeoutException",
        m.py().get_type::<errors::TimeoutException>(),
    )?;
    m.add(
        "ConnectTimeout",
        m.py().get_type::<errors::ConnectTimeout>(),
    )?;
    m.add("ReadTimeout", m.py().get_type::<errors::ReadTimeout>())?;
    m.add("WriteTimeout", m.py().get_type::<errors::WriteTimeout>())?;
    m.add("PoolTimeout", m.py().get_type::<errors::PoolTimeout>())?;
    m.add("NetworkError", m.py().get_type::<errors::NetworkError>())?;
    m.add("ConnectError", m.py().get_type::<errors::ConnectError>())?;
    m.add("ReadError", m.py().get_type::<errors::ReadError>())?;
    m.add("WriteError", m.py().get_type::<errors::WriteError>())?;
    m.add("CloseError", m.py().get_type::<errors::CloseError>())?;
    m.add("ProtocolError", m.py().get_type::<errors::ProtocolError>())?;
    m.add(
        "LocalProtocolError",
        m.py().get_type::<errors::LocalProtocolError>(),
    )?;
    m.add(
        "RemoteProtocolError",
        m.py().get_type::<errors::RemoteProtocolError>(),
    )?;
    m.add("ProxyError", m.py().get_type::<errors::ProxyError>())?;
    m.add(
        "UnsupportedProtocol",
        m.py().get_type::<errors::UnsupportedProtocol>(),
    )?;
    m.add("DecodingError", m.py().get_type::<errors::DecodingError>())?;
    m.add(
        "TooManyRedirects",
        m.py().get_type::<errors::TooManyRedirects>(),
    )?;
    m.add(
        "HTTPStatusError",
        m.py().get_type::<errors::HTTPStatusError>(),
    )?;
    m.add("InvalidURL", m.py().get_type::<errors::InvalidURL>())?;
    m.add(
        "CookieConflict",
        m.py().get_type::<errors::CookieConflict>(),
    )?;
    m.add("StreamError", m.py().get_type::<errors::StreamError>())?;
    m.add(
        "StreamConsumed",
        m.py().get_type::<errors::StreamConsumed>(),
    )?;
    m.add(
        "ResponseNotRead",
        m.py().get_type::<errors::ResponseNotRead>(),
    )?;
    m.add(
        "RequestNotRead",
        m.py().get_type::<errors::RequestNotRead>(),
    )?;
    m.add("StreamClosed", m.py().get_type::<errors::StreamClosed>())?;

    macro_rules! http_no_client {
    ($($name:ident),*) => {
        $(
            #[pyfunction]
            #[pyo3(signature = (url, content=None, data=None, headers=None, timeout=None, force_http3=false, cookie_jar=None, cookies=None))]
            fn $name(
                _py: Python,
                url: String,
                content: Option<Vec<u8>>,
                data: Option<RequestBody>,
                headers: Option<HashMap<String, String>>,
                timeout: Option<f64>,
                force_http3: Option<bool>,
                cookie_jar: Option<pyo3::Bound<'_, pyo3::PyAny>>,
                cookies: Option<pyo3::Bound<'_, pyo3::PyAny>>,
            ) -> Result<response::ImpitPyResponse, errors::ImpitPyError> {
                let client = Client::new(_py, None, None, None, None, None, None, None, None, cookie_jar, cookies, None, None);

                client?.$name(_py, url, content, data, headers, timeout, force_http3)
            }

            m.add_function(wrap_pyfunction!($name, m)?)?;
        )*
    };
}

    http_no_client!(get, post, put, head, patch, delete, options, trace);

    Ok(())
}
